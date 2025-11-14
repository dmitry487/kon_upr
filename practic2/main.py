#!/usr/bin/env python3
"""
ПОЛНАЯ РЕАЛИЗАЦИЯ ИНСТРУМЕНТА ВИЗУАЛИЗАЦИИ ГРАФА ЗАВИСИМОСТЕЙ ДЛЯ NUGET
ВСЕ 5 ЭТАПОВ В ОДНОМ ФАЙЛЕ

ЭТАП 1: Минимальный прототип с конфигурацией
ЭТАП 2: Сбор данных о зависимостях  
ЭТАП 3: Основные операции с графом (BFS, фильтрация, циклы)
ЭТАП 4: Обратные зависимости
ЭТАП 5: Визуализация (Graphviz, SVG, ASCII-дерево)
"""

import argparse
import sys
import os
import json
import urllib.request
import urllib.parse
import urllib.error
import xml.etree.ElementTree as ET
from collections import deque, defaultdict
from typing import Dict, List, Set, Optional, Tuple
import subprocess
import tempfile

class DependencyVisualizer:
    """
    ГЛАВНЫЙ КЛАСС ПРИЛОЖЕНИЯ - РЕАЛИЗУЕТ ВСЕ 5 ЭТАПОВ
    
    Этап 1: Конфигурация через аргументы командной строки
    Этап 2: Получение данных из NuGet репозитория
    Этап 3: Построение графа BFS с обработкой циклов и фильтрацией
    Этап 4: Поиск обратных зависимостей
    Этап 5: Визуализация через Graphviz и ASCII-дерево
    """
    
    def __init__(self):
        """Инициализация всех структур данных для работы приложения"""
        # Конфигурация из командной строки (ЭТАП 1)
        self.config = {}
        
        # Граф зависимостей: пакет -> список зависимостей (ЭТАП 2,3)
        self.dependency_graph = defaultdict(list)
        
        # Обратный граф: пакет -> кто от него зависит (ЭТАП 4)  
        self.reverse_dependency_graph = defaultdict(list)
        
        # Множество посещенных пакетов для обхода (ЭТАП 3)
        self.visited_packages = set()
        
        # Флаг обнаружения циклических зависимостей (ЭТАП 3)
        self.cycle_detected = False
        
        # Кэш для хранения данных о пакетах (оптимизация ЭТАП 2)
        self.package_cache = {}
        
        # Счетчик глубины рекурсии для ограничения (ЭТАП 3)
        self.recursion_depth = 0
        self.max_recursion_depth = 20

    # =========================================================================
    # ЭТАП 1: КОНФИГУРАЦИЯ И АРГУМЕНТЫ КОМАНДНОЙ СТРОКИ
    # =========================================================================
    
    def parse_arguments(self) -> argparse.Namespace:
        """
        ПАРСИНГ АРГУМЕНТОВ КОМАНДНОЙ СТРОКИ - ОСНОВА ЭТАПА 1
        
        Все параметры соответствуют техническому заданию этапа 1.
        Обязательные параметры: --package, --source
        Остальные параметры имеют значения по умолчанию.
        """
        parser = argparse.ArgumentParser(
            description='Инструмент визуализации графа зависимостей NuGet пакетов',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Примеры использования:
  # Реальный репозиторий (ЭТАП 2)
  python dependency_visualizer.py --package Newtonsoft.Json --source https://api.nuget.org/v3/index.json
  
  # Тестовый режим с ASCII-деревом (ЭТАП 3,5)
  python dependency_visualizer.py --package A --source test_repo.txt --test-mode --ascii-tree
  
  # Обратные зависимости (ЭТАП 4)
  python dependency_visualizer.py --package B --source test_repo.txt --test-mode --reverse
  
  # Полная конфигурация с фильтром (ЭТАП 1,3)
  python dependency_visualizer.py --package MyPackage --source repo.txt --test-mode --version 1.0.0 --output graph.svg --ascii-tree --filter Test
            """
        )
        
        # ОБЯЗАТЕЛЬНЫЕ ПАРАМЕТРЫ - должны быть всегда указаны
        parser.add_argument(
            '--package',
            required=True,
            type=str,
            help='Имя анализируемого пакета (например: Newtonsoft.Json)'
        )
        
        parser.add_argument(
            '--source', 
            required=True,
            type=str,
            help='URL репозитория NuGet или путь к тестовому файлу'
        )
        
        # ОПЦИОНАЛЬНЫЕ ПАРАМЕТРЫ - настройки работы приложения
        parser.add_argument(
            '--test-mode',
            action='store_true',
            default=False,
            help='Режим работы с тестовым репозиторием (файл вместо URL)'
        )
        
        parser.add_argument(
            '--version',
            default='latest', 
            type=str,
            help='Версия анализируемого пакета (по умолчанию: latest)'
        )
        
        parser.add_argument(
            '--output',
            default='dependencies.svg',
            type=str,
            help='Имя файла для сохранения графа в формате SVG'
        )
        
        parser.add_argument(
            '--ascii-tree',
            action='store_true', 
            default=False,
            help='Вывести дерево зависимостей в ASCII-формате в консоль'
        )
        
        parser.add_argument(
            '--filter',
            default='',
            type=str,
            help='Фильтр пакетов: исключить пакеты содержащие эту подстроку'
        )
        
        parser.add_argument(
            '--reverse',
            action='store_true',
            default=False, 
            help='Режим обратных зависимостей: найти кто зависит от указанного пакета'
        )
        
        return parser.parse_args()
    
    def validate_arguments(self, args: argparse.Namespace) -> List[str]:
        """
        ПРОВЕРКА КОРРЕКТНОСТИ АРГУМЕНТОВ - ЧАСТЬ ЭТАПА 1
        
        Выполняет валидацию всех входных параметров:
        - Проверка обязательных полей
        - Проверка существования файлов в тестовом режиме
        - Проверка возможности создания выходных файлов
        - Дополнительные проверки специфичные для параметров
        """
        errors = []
        
        # Проверка обязательных параметров на пустоту
        if not args.package or not args.package.strip():
            errors.append("Имя пакета не может быть пустым")
            
        if not args.source or not args.source.strip():
            errors.append("Источник данных не может быть пустым")
        
        # В тестовом режиме проверяем что файл существует
        if args.test_mode:
            if not os.path.exists(args.source):
                errors.append(f"Тестовый файл не найден: {args.source}")
            elif not os.path.isfile(args.source):
                errors.append(f"Источник в тестовом режиме должен быть файлом: {args.source}")
        
        # Проверка возможности записи выходного файла
        if args.output:
            output_dir = os.path.dirname(args.output) or '.'
            if not os.path.exists(output_dir):
                try:
                    os.makedirs(output_dir, exist_ok=True)
                except Exception as e:
                    errors.append(f"Не удается создать директорию для выходного файла: {e}")
            elif not os.access(output_dir, os.W_OK):
                errors.append(f"Нет прав на запись в директорию: {output_dir}")
        
        return errors
    
    def print_config(self, args: argparse.Namespace) -> None:
        """
        ВЫВОД КОНФИГУРАЦИИ - ТРЕБОВАНИЕ ЭТАПА 1
        
        Отображает все настройки приложения в формате ключ-значение.
        Пользователь видит как именно будет работать программа.
        """
        print("╔══════════════════════════════════════════════════════════════╗")
        print("║                    КОНФИГУРАЦИЯ ПРИЛОЖЕНИЯ                  ║")
        print("╠══════════════════════════════════════════════════════════════╣")
        print(f"║ 📦  Имя пакета:          {args.package:<35} ║")
        print(f"║ 🔗  Источник:            {args.source:<35} ║")
        print(f"║ 🧪  Режим тестирования:  {'Да':<35} ║" if args.test_mode else 
              f"║ 🧪  Режим тестирования:  {'Нет':<35} ║")
        print(f"║ 🔢  Версия пакета:       {args.version:<35} ║")
        print(f"║ 💾  Выходной файл:       {args.output:<35} ║")
        print(f"║ 🌳  ASCII-дерево:        {'Да':<35} ║" if args.ascii_tree else 
              f"║ 🌳  ASCII-дерево:        {'Нет':<35} ║")
        print(f"║ 🔍  Фильтр пакетов:      {args.filter if args.filter else 'Не задан':<35} ║")
        print(f"║ 🔄  Обратные зависимости:{'Да':<35} ║" if args.reverse else 
              f"║ 🔄  Обратные зависимости:{'Нет':<35} ║")
        print("╚══════════════════════════════════════════════════════════════╝")

    # =========================================================================
    # ЭТАП 2: СБОР ДАННЫХ О ЗАВИСИМОСТЯХ ИЗ NUGET РЕПОЗИТОРИЯ
    # =========================================================================
    
    def get_nuget_service_index(self, source_url: str) -> Dict:
        """
        ПОЛУЧЕНИЕ ИНДЕКСА СЕРВИСА NUGET - ОСНОВА ЭТАПА 2
        
        NuGet v3 API предоставляет индекс сервиса со списком доступных endpoint-ов.
        Этот метод загружает и парсит JSON индекс для поиска нужных URL.
        """
        try:
            # Создаем HTTP запрос к NuGet API
            req = urllib.request.Request(
                source_url,
                headers={'User-Agent': 'DependencyVisualizer/1.0'}
            )
            
            # Выполняем запрос с таймаутом 30 секунд
            with urllib.request.urlopen(req, timeout=30) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}: {response.reason}")
                
                # Читаем и парсим JSON ответ
                data = json.loads(response.read().decode('utf-8'))
                return data
                
        except urllib.error.URLError as e:
            raise Exception(f"Ошибка подключения к репозиторию: {e}")
        except json.JSONDecodeError as e:
            raise Exception(f"Ошибка парсинга JSON индекса: {e}")
        except Exception as e:
            raise Exception(f"Ошибка получения индекса сервиса: {e}")
    
    def find_package_base_url(self, service_index: Dict) -> str:
        """
        ПОИСК БАЗОВОГО URL ДЛЯ ДОСТУПА К ПАКЕТАМ - ЧАСТЬ ЭТАПА 2
        
        В индекс сервиса ищем endpoint типа 'PackageBaseAddress/3.0.0'
        который предоставляет доступ к файлам пакетов.
        """
        for resource in service_index.get('resources', []):
            resource_type = resource.get('@type', '')
            # Ищем endpoint для доступа к пакетам
            if resource_type.startswith('PackageBaseAddress'):
                return resource['@id']
        
        raise Exception("В индекс сервиса не найден PackageBaseAddress endpoint")
    
    def get_package_versions(self, package_name: str, base_url: str) -> List[str]:
        """
        ПОЛУЧЕНИЕ СПИСКА ДОСТУПНЫХ ВЕРСИЙ ПАКЕТА - ЧАСТЬ ЭТАПА 2
        
        Обращается к NuGet API для получения всех версий указанного пакета.
        Версии возвращаются в отсортированном порядке.
        """
        try:
            # Формируем URL для получения версий пакета
            # NuGet API требует lowercase имени пакета
            package_name_lower = package_name.lower()
            url = f"{base_url}{package_name_lower}/index.json"
            
            with urllib.request.urlopen(url, timeout=30) as response:
                data = json.loads(response.read().decode('utf-8'))
                versions = data.get('versions', [])
                
                # Сортируем версии для удобства
                versions.sort()
                return versions
                
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise Exception(f"Пакет не найден: {package_name}")
            else:
                raise Exception(f"HTTP ошибка при получении версий: {e.code}")
        except Exception as e:
            raise Exception(f"Ошибка получения версий пакета {package_name}: {e}")
    
    def get_package_nuspec(self, package_name: str, version: str, base_url: str) -> str:
        """
        ПОЛУЧЕНИЕ NUSpec ФАЙЛА ПАКЕТА - ОСНОВНОЙ МЕТОД ЭТАПА 2
        
        NUSpec файл содержит метаданные пакета включая зависимости.
        Этот метод загружает .nuspec файл для указанной версии пакета.
        """
        try:
            # Формируем URL для загрузки .nuspec файла
            package_name_lower = package_name.lower()
            url = f"{base_url}{package_name_lower}/{version}/{package_name_lower}.nuspec"
            
            with urllib.request.urlopen(url, timeout=30) as response:
                # Возвращаем содержимое XML файла
                return response.read().decode('utf-8')
                
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise Exception(f"Версия {version} пакета {package_name} не найдена")
            else:
                raise Exception(f"HTTP ошибка при загрузке nuspec: {e.code}")
        except Exception as e:
            raise Exception(f"Ошибка загрузки nuspec для {package_name} {version}: {e}")
    
    def parse_dependencies_from_nuspec(self, nuspec_content: str) -> List[str]:
        """
        ПАРСИНГ ЗАВИСИМОСТЕЙ ИЗ NUSpec XML - КЛЮЧЕВАЯ ЧАСТЬ ЭТАПА 2
        
        Анализирует XML структуру .nuspec файла и извлекает список зависимостей.
        Зависимости находятся в теге <dependencies> внутри <metadata>.
        """
        dependencies = []
        
        try:
            # Парсим XML содержимое
            root = ET.fromstring(nuspec_content)
            
            # Определяем namespace для NuGet XML
            ns = {'nuspec': 'http://schemas.microsoft.com/packaging/2013/05/nuspec.xsd'}
            
            # Ищем раздел metadata с информацией о пакете
            metadata = root.find('nuspec:metadata', ns)
            if metadata is None:
                return dependencies  # Нет metadata - нет зависимостей
            
            # Ищем раздел dependencies внутри metadata
            dependencies_elem = metadata.find('nuspec:dependencies', ns)
            if dependencies_elem is None:
                return dependencies  # Нет dependencies - пустой список
            
            # Извлекаем все dependency элементы
            for dep_elem in dependencies_elem.findall('nuspec:dependency', ns):
                dep_id = dep_elem.get('id')
                if dep_id and dep_id.strip():
                    # Добавляем имя пакета в список зависимостей
                    dependencies.append(dep_id.strip())
            
        except ET.ParseError as e:
            print(f"Предупреждение: ошибка парсинга XML nuspec: {e}")
        except Exception as e:
            print(f"Предупреждение: ошибка извлечения зависимостей: {e}")
        
        return dependencies

    def get_direct_dependencies(self, package_name: str, version: str) -> List[str]:
        """
        ПОЛУЧЕНИЕ ПРЯМЫХ ЗАВИСИМОСТЕЙ ПАКЕТА - ГЛАВНЫЙ РЕЗУЛЬТАТ ЭТАПА 2
        
        Объединяет все методы этапа 2 для получения списка зависимостей:
        1. Получение индекс сервиса
        2. Поиск базового URL  
        3. Получение версий (если нужно)
        4. Загрузка и парсинг nuspec
        5. Извлечение зависимостей
        """
        # Если пакет уже в кэше - возвращаем из кэша
        cache_key = f"{package_name}@{version}"
        if cache_key in self.package_cache:
            return self.package_cache[cache_key]
        
        dependencies = []
        
        try:
            # Получаем индекс сервиса NuGet
            service_index = self.get_nuget_service_index(self.config['source'])
            
            # Находим базовый URL для доступа к пакетам
            base_url = self.find_package_base_url(service_index)
            
            # Если версия 'latest' - находим последнюю версию
            actual_version = version
            if version == 'latest':
                versions = self.get_package_versions(package_name, base_url)
                if versions:
                    actual_version = versions[-1]  # Последняя версия
                else:
                    raise Exception(f"Не найдены версии пакета {package_name}")
            
            # Загружаем и парсим nuspec файл
            nuspec_content = self.get_package_nuspec(package_name, actual_version, base_url)
            dependencies = self.parse_dependencies_from_nuspec(nuspec_content)
            
            # Сохраняем в кэш для повторного использования
            self.package_cache[cache_key] = dependencies
            
        except Exception as e:
            print(f"Ошибка получения зависимостей для {package_name}: {e}")
        
        return dependencies

    # =========================================================================
    # ЭТАП 3: ОСНОВНЫЕ ОПЕРАЦИИ С ГРАФОМ ЗАВИСИМОСТЕЙ
    # =========================================================================
    
    def load_test_repository(self, file_path: str) -> Dict[str, List[str]]:
        """
        ЗАГРУЗКА ТЕСТОВОГО РЕПОЗИТОРИЯ - ЧАСТЬ ЭТАПА 3
        
        Тестовый репозиторий представляет собой текстовый файл формата:
        ПакетА:Зависимость1,Зависимость2
        ПакетБ:Зависимость3
        ПакетВ:  (нет зависимостей)
        """
        graph = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # Пропускаем пустые строки и комментарии
                    if not line or line.startswith('#'):
                        continue
                    
                    # Разделяем пакет и зависимости
                    if ':' in line:
                        package_part, deps_part = line.split(':', 1)
                        package = package_part.strip()
                        
                        # Обрабатываем зависимости
                        dependencies = []
                        if deps_part.strip():  # Если есть зависимости
                            for dep in deps_part.split(','):
                                dep_clean = dep.strip()
                                if dep_clean:  # Не пустая зависимость
                                    dependencies.append(dep_clean)
                        
                        graph[package] = dependencies
                    else:
                        print(f"Предупреждение: строка {line_num} имеет неверный формат: {line}")
                        
        except Exception as e:
            raise Exception(f"Ошибка загрузки тестового репозитория: {e}")
        
        return graph

    def should_filter_package(self, package_name: str) -> bool:
        """
        ПРОВЕРКА ФИЛЬТРАЦИИ ПАКЕТА - ЧАСТЬ ЭТАПА 3
        
        Возвращает True если пакет должен быть отфильтрован (исключен из анализа).
        Фильтрация происходит по подстроке указанной в --filter.
        """
        if not self.config.get('filter'):
            return False  # Фильтр не задан - не фильтруем
        
        return self.config['filter'] in package_name

    def bfs_build_dependency_graph(self, start_package: str, version: str = 'latest', 
                                 path: List[str] = None) -> None:
        """
        ПОСТРОЕНИЕ ГРАФА ЗАВИСИМОСТЕЙ BFS С РЕКУРСИЕЙ - ОСНОВА ЭТАПА 3
        
        Алгоритм обхода в ширину с рекурсией для построения полного графа зависимостей.
        Обрабатывает циклические зависимости и ограничивает глубину рекурсии.
        
        Логика работы:
        1. Проверка циклических зависимостей
        2. Проверка глубины рекурсии  
        3. Получение зависимостей текущего пакета
        4. Фильтрация зависимостей
        5. Рекурсивный обход зависимостей
        6. Построение обратного графа
        """
        # Инициализация пути для отслеживания циклов
        if path is None:
            path = []
        
        # ПРОВЕРКА 1: ОБНАРУЖЕНИЕ ЦИКЛИЧЕСКИХ ЗАВИСИМОСТЕЙ
        if start_package in path:
            cycle_path = ' -> '.join(path + [start_package])
            print(f"⚠️  Обнаружена циклическая зависимость: {cycle_path}")
            self.cycle_detected = True
            return
        
        # ПРОВЕРКА 2: ОГРАНИЧЕНИЕ ГЛУБИНЫ РЕКУРСИИ
        self.recursion_depth += 1
        if self.recursion_depth > self.max_recursion_depth:
            print(f"⚠️  Достигнута максимальная глубина рекурсии ({self.max_recursion_depth}) для пакета {start_package}")
            self.recursion_depth -= 1
            return
        
        # ПРОВЕРКА 3: ПРОПУСК УЖЕ ОБРАБОТАННЫХ ПАКЕТОВ
        if start_package in self.visited_packages:
            self.recursion_depth -= 1
            return
        
        # Отмечаем пакет как посещенный
        self.visited_packages.add(start_package)
        
        # ШАГ 1: ПОЛУЧЕНИЕ ЗАВИСИМОСТЕЙ ТЕКУЩЕГО ПАКЕТА
        dependencies = []
        if self.config.get('test_mode'):
            # РЕЖИМ ТЕСТИРОВАНИЯ: загрузка из файла
            test_graph = self.load_test_repository(self.config['source'])
            dependencies = test_graph.get(start_package, [])
        else:
            # РЕАЛЬНЫЙ РЕЖИМ: получение из NuGet репозитория
            dependencies = self.get_direct_dependencies(start_package, version)
        
        # Вывод прямых зависимостей (требование этапа 2)
        if self.recursion_depth == 1:  # Только для корневого пакета
            print(f"📦 Прямые зависимости пакета {start_package}:")
            if dependencies:
                for dep in dependencies:
                    print(f"   ├── {dep}")
            else:
                print("   └── (нет зависимостей)")
        
        # ШАГ 2: ФИЛЬТРАЦИЯ ЗАВИСИМОСТЕЙ
        filtered_dependencies = []
        for dep in dependencies:
            if not self.should_filter_package(dep):
                filtered_dependencies.append(dep)
            else:
                print(f"🚫 Пакет отфильтрован: {dep}")
        
        # ШАГ 3: ДОБАВЛЕНИЕ В ГРАФ ЗАВИСИМОСТЕЙ
        self.dependency_graph[start_package] = filtered_dependencies
        
        # ШАГ 4: ПОСТРОЕНИЕ ОБРАТНОГО ГРАФА (для этапа 4)
        for dep in filtered_dependencies:
            self.reverse_dependency_graph[dep].append(start_package)
        
        # ШАГ 5: РЕКУРСИВНЫЙ ОБХОД ЗАВИСИМОСТЕЙ
        new_path = path + [start_package]
        for dep in filtered_dependencies:
            self.bfs_build_dependency_graph(dep, 'latest', new_path)
        
        # Восстанавливаем глубину рекурсии
        self.recursion_depth -= 1

    # =========================================================================
    # ЭТАП 4: ОБРАТНЫЕ ЗАВИСИМОСТИ
    # =========================================================================
    
    def find_reverse_dependencies(self, target_package: str) -> List[str]:
        """
        ПОИСК ОБРАТНЫХ ЗАВИСИМОСТЕЙ - ОСНОВА ЭТАПА 4
        
        Обратные зависимости - это пакеты, которые зависят от указанного пакета.
        Использует BFS обход для поиска всех пакетов, зависящих от целевого.
        
        Алгоритм:
        1. Используем очередь для BFS обхода
        2. Начинаем с целевого пакета  
        3. Ищем в обратном графе кто зависит от текущего пакета
        4. Добавляем найденные пакеты в результат и очередь
        """
        # Множество для отслеживания посещенных пакетов
        visited = set()
        # Очередь для BFS обхода
        queue = deque([target_package])
        # Результат - список обратных зависимостей
        reverse_deps = []
        
        while queue:
            current_package = queue.popleft()
            
            # Пропускаем уже посещенные пакеты
            if current_package in visited:
                continue
                
            visited.add(current_package)
            
            # Ищем пакеты, которые зависят от текущего
            dependents = self.reverse_dependency_graph.get(current_package, [])
            
            for dependent in dependents:
                if dependent not in visited:
                    # Добавляем в результат (кроме самого target_package)
                    if dependent != target_package:
                        reverse_deps.append(dependent)
                    # Добавляем в очередь для продолжения обхода
                    queue.append(dependent)
        
        return reverse_deps

    def get_reverse_dependencies_for_package(self, package_name: str) -> List[str]:
        """
        ПОЛУЧЕНИЕ ОБРАТНЫХ ЗАВИСИМОСТЕЙ ДЛЯ УКАЗАННОГО ПАКЕТА - ЭТАП 4
        
        В режиме тестирования использует тестовый репозиторий.
        В реальном режиме использует построенный обратный граф.
        """
        if self.config.get('test_mode'):
            # В ТЕСТОВОМ РЕЖИМЕ: ищем обратные зависимости в тестовом графе
            test_graph = self.load_test_repository(self.config['source'])
            reverse_deps = []
            
            for pkg, deps in test_graph.items():
                if package_name in deps:
                    reverse_deps.append(pkg)
            
            return reverse_deps
        else:
            # В РЕАЛЬНОМ РЕЖИМЕ: используем обратный граф
            return self.find_reverse_dependencies(package_name)

    # =========================================================================
    # ЭТАП 5: ВИЗУАЛИЗАЦИЯ ГРАФА ЗАВИСИМОСТЕЙ
    # =========================================================================
    
    def print_ascii_tree(self, start_package: str, visited: Set[str] = None, 
                        prefix: str = "", is_last: bool = True) -> None:
        """
        ВЫВОД ASCII-ДЕРЕВА ЗАВИСИМОСТЕЙ - ЧАСТЬ ЭТАПА 5
        
        Рекурсивно строит дерево зависимостей в текстовом виде.
        Использует Unicode символы для визуального представления иерархии.
        
        Символы:
        ├── : ветвь продолжается
        └── : последняя ветвь  
        │   : вертикальная линия
            : отступ
        """
        if visited is None:
            visited = set()
        
        # ПРОВЕРКА ЦИКЛИЧЕСКИХ ЗАВИСИМОСТЕЙ В ДЕРЕВЕ
        if start_package in visited:
            connector = "└── " if is_last else "├── "
            print(f"{prefix}{connector}{start_package} 🔁 (циклическая зависимость)")
            return
        
        visited.add(start_package)
        
        # ВЫВОД ТЕКУЩЕГО ПАКЕТА
        connector = "└── " if is_last else "├── "
        print(f"{prefix}{connector}{start_package}")
        
        # ПОЛУЧЕНИЕ ЗАВИСИМОСТЕЙ ТЕКУЩЕГО ПАКЕТА
        dependencies = self.dependency_graph.get(start_package, [])
        
        # РЕКУРСИВНЫЙ ВЫВОД ЗАВИСИМОСТЕЙ
        for i, dep in enumerate(dependencies):
            is_last_dep = (i == len(dependencies) - 1)
            # Формируем префикс для следующего уровня
            new_prefix = prefix + ("    " if is_last else "│   ")
            self.print_ascii_tree(dep, visited.copy(), new_prefix, is_last_dep)
    
    def generate_graphviz(self) -> str:
        """
        ГЕНЕРАЦИЯ GRAPHVIZ КОДА - ОСНОВА ЭТАПА 5
        
        Создает описание графа на языке DOT для Graphviz.
        Формат: digraph с направленными ребрами от пакета к зависимостям.
        
        Структура DOT файла:
        digraph Dependencies {
            rankdir=TB;           // Ориентация сверху вниз
            node [shape=box];     // Форма узлов - прямоугольник
            A -> B;              // Зависимость A от B
            A -> C;
            B -> D;
        }
        """
        lines = []
        
        # ЗАГОЛОВОК GRAPHVIZ
        lines.append('digraph Dependencies {')
        lines.append('    rankdir=TB;')                    # Ориентация сверху вниз
        lines.append('    node [shape=box, style=filled, fillcolor=lightblue];')  # Стиль узлов
        lines.append('    edge [arrowsize=0.8];')          # Размер стрелок
        
        # НАСТРОЙКИ ШРИФТА
        lines.append('    graph [fontname="Arial"];')
        lines.append('    node [fontname="Arial"];')
        lines.append('    edge [fontname="Arial"];')
        
        # СОЗДАНИЕ УЗЛОВ И РЕБЕР
        edges_added = set()  # Множество для избежания дубликатов
        
        for package, dependencies in self.dependency_graph.items():
            # Пропускаем отфильтрованные пакеты
            if self.should_filter_package(package):
                continue
                
            # Добавляем ребра зависимостей
            for dep in dependencies:
                # Пропускаем отфильтрованные зависимости
                if self.should_filter_package(dep):
                    continue
                    
                # Создаем уникальный идентификатор ребра
                edge = f'"{package}" -> "{dep}"'
                if edge not in edges_added:
                    lines.append(f'    {edge};')
                    edges_added.add(edge)
        
        # ЗАВЕРШЕНИЕ GRAPHVIZ КОДА
        lines.append('}')
        
        return '\n'.join(lines)
    
    def save_svg(self, graphviz_content: str, output_file: str) -> bool:
        """
        СОХРАНЕНИЕ ГРАФА В SVG ФАЙЛ - ЧАСТЬ ЭТАПА 5
        
        Использует системную утилиту Graphviz (dot) для преобразования
        DOT-описания в SVG изображение.
        
        Процесс:
        1. Сохраняем DOT-файл во временную директорию
        2. Вызываем 'dot -Tsvg' для конвертации
        3. Сохраняем результат в указанный файл
        4. Удаляем временные файлы
        """
        try:
            # СОЗДАНИЕ ВРЕМЕННОГО DOT-ФАЙЛА
            dot_file = output_file.replace('.svg', '.dot')
            with open(dot_file, 'w', encoding='utf-8') as f:
                f.write(graphviz_content)
            
            print(f"📝 Graphviz DOT файл сохранен: {dot_file}")
            
            # ПРОВЕРКА НАЛИЧИЯ GRAPHVIZ
            try:
                # Проверяем доступность утилиты dot
                subprocess.run(['dot', '-V'], capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("❌ Graphviz не установлен или не доступен в PATH")
                print("💡 Установите Graphviz: https://graphviz.org/download/")
                print("📋 DOT описание сохранено, SVG не сгенерирован")
                return False
            
            # КОНВЕРТАЦИЯ DOT -> SVG
            print("🔄 Конвертация DOT в SVG...")
            result = subprocess.run([
                'dot', '-Tsvg', dot_file, '-o', output_file
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print(f"🎨 SVG граф сохранен: {output_file}")
                
                # УДАЛЕНИЕ ВРЕМЕННОГО DOT-ФАЙЛА (опционально)
                try:
                    os.remove(dot_file)
                    print(f"🗑️  Временный DOT файл удален: {dot_file}")
                except:
                    pass  # Не критично если не удалось удалить
                    
                return True
            else:
                print(f"❌ Ошибка конвертации в SVG: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ Таймаут конвертации SVG - граф слишком сложный")
            return False
        except Exception as e:
            print(f"❌ Ошибка сохранения SVG: {e}")
            return False
    
    def demonstrate_examples(self) -> None:
        """
        ДЕМОНСТРАЦИЯ ПРИМЕРОВ - ТРЕБОВАНИЕ ЭТАПА 5
        
        Запускает анализ трех различных пакетов для демонстрации функциональности.
        Показывает различные сценарии работы инструмента.
        """
        examples = [
            {"package": "Newtonsoft.Json", "version": "13.0.1", "desc": "Популярный JSON serializer"},
            {"package": "EntityFramework", "version": "6.4.4", "desc": "ORM от Microsoft"},
            {"package": "NUnit", "version": "3.14.0", "desc": "Фреймворк для unit-тестирования"}
        ]
        
        print("\n" + "="*70)
        print("ДЕМОНСТРАЦИЯ РАБОТЫ С РАЗЛИЧНЫМИ ПАКЕТАМИ")
        print("="*70)
        
        # Сохраняем оригинальную конфигурацию
        original_config = self.config.copy()
        original_graph = self.dependency_graph.copy()
        
        for i, example in enumerate(examples, 1):
            print(f"\n📦 Пример {i}: {example['package']} {example['version']}")
            print(f"   📝 {example['desc']}")
            print("-" * 50)
            
            # Обновляем конфигурацию для демо
            self.config['package'] = example['package']
            self.config['version'] = example['version']
            
            # Сбрасываем состояние графа
            self.dependency_graph.clear()
            self.reverse_dependency_graph.clear()
            self.visited_packages.clear()
            self.cycle_detected = False
            self.recursion_depth = 0
            
            try:
                # Строим граф зависимостей
                self.bfs_build_dependency_graph(example['package'], example['version'])
                
                # Выводим ASCII-дерево если запрошено
                if self.config.get('ascii_tree'):
                    print(f"🌳 ASCII-дерево для {example['package']}:")
                    self.print_ascii_tree(example['package'])
                    print()
                
                # Генерируем и сохраняем SVG
                graphviz_content = self.generate_graphviz()
                output_file = f"{example['package'].lower().replace('.', '_')}_dependencies.svg"
                
                if self.save_svg(graphviz_content, output_file):
                    print(f"✅ Граф сохранен: {output_file}")
                else:
                    print(f"⚠️  Не удалось сохранить граф: {output_file}")
                
                # Выводим статистику
                total_packages = len(self.dependency_graph)
                print(f"📊 Статистика: {total_packages} пакетов в графе")
                
                if self.cycle_detected:
                    print("🔄 Обнаружены циклические зависимости")
                    
            except Exception as e:
                print(f"❌ Ошибка при обработке {example['package']}: {e}")
        
        # Восстанавливаем оригинальную конфигурацию
        self.config = original_config
        self.dependency_graph = original_graph
        
        print("\n" + "="*70)
        print("ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА")
        print("="*70)

    # =========================================================================
    # ОСНОВНОЙ МЕТОД ЗАПУСКА ПРИЛОЖЕНИЯ
    # =========================================================================
    
    def run(self) -> None:
        """
        ГЛАВНЫЙ МЕТОД ЗАПУСКА - ОБЪЕДИНЯЕТ ВСЕ 5 ЭТАПОВ
        
        Последовательность выполнения:
        1. ЭТАП 1: Парсинг и валидация аргументов
        2. ЭТАП 2: Сбор данных о зависимостях  
        3. ЭТАП 3: Построение графа BFS с фильтрацией
        4. ЭТАП 4: Обратные зависимости (если нужно)
        5. ЭТАП 5: Визуализация (Graphviz, ASCII-дерево)
        """
        try:
            print("🚀 ЗАПУСК ИНСТРУМЕНТА ВИЗУАЛИЗАЦИИ ЗАВИСИМОСТЕЙ")
            print("=" * 70)
            
            # ЭТАП 1: КОНФИГУРАЦИЯ
            print("🔧 ЭТАП 1: Парсинг и валидация аргументов...")
            args = self.parse_arguments()
            
            # Валидация параметров
            errors = self.validate_arguments(args)
            if errors:
                print("❌ Ошибки в параметрах:")
                for error in errors:
                    print(f"   • {error}")
                sys.exit(1)
            
            # Сохраняем конфигурацию
            self.config = vars(args)
            
            # Вывод конфигурации (требование этапа 1)
            self.print_config(args)
            
            # ОСНОВНАЯ ЛОГИКА В ЗАВИСИМОСТИ ОТ РЕЖИМА
            if args.reverse:
                # РЕЖИМ ОБРАТНЫХ ЗАВИСИМОСТЕЙ (ЭТАП 4)
                print(f"\n🔄 ЭТАП 4: Поиск обратных зависимостей для {args.package}")
                
                if args.test_mode:
                    # В тестовом режиме ищем в тестовом файле
                    reverse_deps = self.get_reverse_dependencies_for_package(args.package)
                else:
                    # В реальном режиме сначала строим граф
                    print("📦 Построение графа для поиска обратных зависимостей...")
                    self.bfs_build_dependency_graph(args.package, args.version)
                    reverse_deps = self.get_reverse_dependencies_for_package(args.package)
                
                # Вывод результата
                print(f"📋 Пакеты, зависящие от {args.package}:")
                if reverse_deps:
                    for dep in sorted(reverse_deps):
                        print(f"   ├── {dep}")
                else:
                    print("   └── (обратные зависимости не найдены)")
                    
            else:
                # ОСНОВНОЙ РЕЖИМ: ПОСТРОЕНИЕ И ВИЗУАЛИЗАЦИЯ ГРАФА
                print(f"\n📦 ЭТАП 2: Сбор данных о зависимостях {args.package}...")
                
                # ЭТАП 2+3: ПОСТРОЕНИЕ ГРАФА ЗАВИСИМОСТЕЙ
                self.bfs_build_dependency_graph(args.package, args.version)
                
                # ВЫВОД ИНФОРМАЦИИ О ГРАФЕ
                total_packages = len(self.dependency_graph)
                print(f"\n📊 Граф построен: {total_packages} пакетов")
                
                if self.cycle_detected:
                    print("🔄 В графе обнаружены циклические зависимости")
                
                # ЭТАП 5: ВИЗУАЛИЗАЦИЯ
                print(f"\n🎨 ЭТАП 5: Визуализация графа...")
                
                # ASCII-дерево если запрошено
                if args.ascii_tree:
                    print(f"🌳 ASCII-дерево зависимостей:")
                    print("-" * 40)
                    self.print_ascii_tree(args.package)
                    print("-" * 40)
                
                # Graphviz визуализация
                graphviz_content = self.generate_graphviz()
                self.save_svg(graphviz_content, args.output)
                
                # Демонстрация примеров для реального режима
                if not args.test_mode:
                    self.demonstrate_examples()
            
            # УСПЕШНОЕ ЗАВЕРШЕНИЕ
            print("\n✅ ВСЕ ЭТАПЫ ВЫПОЛНЕНЫ УСПЕШНО!")
            print("=" * 70)
            
        except KeyboardInterrupt:
            print("\n⚠️  Работа прервана пользователем")
            sys.exit(130)
        except Exception as e:
            print(f"\n💥 Критическая ошибка: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

def create_test_repository() -> str:
    """
    СОЗДАНИЕ ТЕСТОВОГО РЕПОЗИТОРИЯ ДЛЯ ДЕМОНСТРАЦИИ
    
    Создает файл с тестовыми данными для проверки всех функций:
    - Прямые зависимости
    - Циклические зависимости  
    - Обратные зависимости
    - Различные сценарии зависимостей
    """
    test_content = """# ТЕСТОВЫЙ РЕПОЗИТОРИЙ ДЛЯ ПРОВЕРКИ ИНСТРУМЕНТА
# Формат: Пакет:Зависимость1,Зависимость2,...

# Простые зависимости
A:B,C
B:D,E
C:F,G
D:H
E:
F:
G:A  # Циклическая зависимость G -> A
H:I,J
I:
J:

# Дополнительные пакеты для тестирования
X:Y,Z
Y:Z
Z:
TestPackage:CommonLib
CommonLib:Utility
Utility:

# Пакеты для тестирования фильтрации
OldPackage:DeprecatedLib
DeprecatedLib:LegacyCode
LegacyCode:
NewPackage:ModernLib
ModernLib:
"""
    
    test_file = "test_repository.txt"
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    return test_file

def main():
    """
    ТОЧКА ВХОДА В ПРИЛОЖЕНИЕ
    
    Запускает приложение в демонстрационном режиме если нет аргументов,
    или в обычном режиме с переданными аргументами.
    """
    if len(sys.argv) == 1:
        # ДЕМОНСТРАЦИОННЫЙ РЕЖИМ - показываем все возможности
        print("🎯 ДЕМОНСТРАЦИОННЫЙ РЕЖИМ")
        print("Создание тестового репозитория...")
        test_file = create_test_repository()
        
        visualizer = DependencyVisualizer()
        
        # ТЕСТ 1: ОСНОВНОЙ РЕЖИМ С ASCII-ДЕРЕВОМ
        print("\n" + "="*70)
        print("ТЕСТ 1: Основной режим с ASCII-деревом")
        print("="*70)
        sys.argv = [
            'dependency_visualizer.py',
            '--package', 'A', 
            '--source', test_file,
            '--test-mode',
            '--ascii-tree',
            '--output', 'test_graph.svg'
        ]
        visualizer.run()
        
        # ТЕСТ 2: РЕЖИМ ОБРАТНЫХ ЗАВИСИМОСТЕЙ
        print("\n" + "="*70)
        print("ТЕСТ 2: Режим обратных зависимостей")
        print("="*70)
        sys.argv = [
            'dependency_visualizer.py', 
            '--package', 'A',
            '--source', test_file,
            '--test-mode',
            '--reverse'
        ]
        visualizer.run()
        
        # ТЕСТ 3: ФИЛЬТРАЦИЯ ПАКЕТОВ
        print("\n" + "="*70)
        print("ТЕСТ 3: Фильтрация пакетов (исключить 'Test')")
        print("="*70)
        sys.argv = [
            'dependency_visualizer.py',
            '--package', 'X',
            '--source', test_file, 
            '--test-mode',
            '--filter', 'Test',
            '--ascii-tree'
        ]
        visualizer.run()
        
        # Удаляем тестовый файл
        try:
            os.remove(test_file)
            print(f"\n🗑️  Тестовый файл удален: {test_file}")
        except:
            pass
            
        print("\n💡 Для работы с реальными пакетами используйте:")
        print('   python dependency_visualizer.py --package "Newtonsoft.Json" --source "https://api.nuget.org/v3/index.json"')
        
    else:
        # ОБЫЧНЫЙ РЕЖИМ РАБОТЫ
        visualizer = DependencyVisualizer()
        visualizer.run()

if __name__ == "__main__":
    main()
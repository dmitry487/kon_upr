#!/usr/bin/env python3
"""
Полная реализация инструмента визуализации графа зависимостей для NuGet
Все 5 этапов в одном файле

Этап 1: Минимальный прототип с конфигурацией
Этап 2: Сбор данных о зависимостях
Этап 3: Основные операции с графом (BFS, фильтрация, циклы)
Этап 4: Обратные зависимости
Этап 5: Визуализация (Graphviz DOT, ASCII-дерево)
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

class DependencyVisualizer:
    """
    Главный класс приложения - реализует все 5 этапов
    """
    
    def __init__(self):
        """Инициализация всех структур данных для работы приложения"""
        # Конфигурация из командной строки (Этап 1)
        self.config = {}
        
        # Граф зависимостей: пакет -> список зависимостей (Этап 2,3)
        self.dependency_graph = defaultdict(list)
        
        # Обратный граф: пакет -> кто от него зависит (Этап 4)  
        self.reverse_dependency_graph = defaultdict(list)
        
        # Множество посещенных пакетов для обхода (Этап 3)
        self.visited_packages = set()
        
        # Флаг обнаружения циклических зависимостей (Этап 3)
        self.cycle_detected = False
        
        # Кэш для хранения данных о пакетах (оптимизация Этап 2)
        self.package_cache = {}
        
        # Счетчик глубины рекурсии для ограничения (Этап 3)
        self.recursion_depth = 0
        self.max_recursion_depth = 20

    # =========================================================================
    # ЭТАП 1: КОНФИГУРАЦИЯ И АРГУМЕНТЫ КОМАНДНОЙ СТРОКИ
    # =========================================================================
    
    def parse_arguments(self) -> argparse.Namespace:
        """
        Парсинг аргументов командной строки - основа Этапа 1
        """
        parser = argparse.ArgumentParser(
            description='Инструмент визуализации графа зависимостей NuGet пакетов',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Примеры использования:
  # Реальный репозиторий (Этап 2)
  python dependency_visualizer.py --package Newtonsoft.Json --source https://api.nuget.org/v3/index.json
  
  # Тестовый режим с ASCII-деревом (Этап 3,5)
  python dependency_visualizer.py --package A --source test_repo.txt --test-mode --ascii-tree
  
  # Обратные зависимости (Этап 4)
  python dependency_visualizer.py --package B --source test_repo.txt --test-mode --reverse
  
  # Полная конфигурация с фильтром (Этап 1,3)
  python dependency_visualizer.py --package MyPackage --source repo.txt --test-mode --version 1.0.0 --output graph.dot --ascii-tree --filter Test
            """
        )
        
        # ОБЯЗАТЕЛЬНЫЕ ПАРАМЕТРЫ
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
        
        # ОПЦИОНАЛЬНЫЕ ПАРАМЕТРЫ
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
            default='dependencies.dot',
            type=str,
            help='Имя файла для сохранения графа в формате DOT'
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
        Проверка корректности аргументов - часть Этапа 1
        """
        errors = []
        
        if not args.package or not args.package.strip():
            errors.append("Имя пакета не может быть пустым")
            
        if not args.source or not args.source.strip():
            errors.append("Источник данных не может быть пустым")
        
        if args.test_mode:
            if not os.path.exists(args.source):
                errors.append(f"Тестовый файл не найден: {args.source}")
            elif not os.path.isfile(args.source):
                errors.append(f"Источник в тестовом режиме должен быть файлом: {args.source}")
        
        if args.output:
            output_dir = os.path.dirname(args.output) or '.'
            if not os.path.exists(output_dir):
                try:
                    os.makedirs(output_dir, exist_ok=True)
                except Exception as e:
                    errors.append(f"Не удается создать директорию для выходного файла: {e}")
        
        return errors
    
    def print_config(self, args: argparse.Namespace) -> None:
        """
        Вывод конфигурации - требование Этапа 1
        """
        print("КОНФИГУРАЦИЯ ПРИЛОЖЕНИЯ:")
        print("----------------------")
        print(f"Имя пакета:          {args.package}")
        print(f"Источник:            {args.source}")
        print(f"Режим тестирования:  {'Да' if args.test_mode else 'Нет'}")
        print(f"Версия пакета:       {args.version}")
        print(f"Выходной файл:       {args.output}")
        print(f"ASCII-дерево:        {'Да' if args.ascii_tree else 'Нет'}")
        print(f"Фильтр пакетов:      {args.filter if args.filter else 'Не задан'}")
        print(f"Обратные зависимости:{'Да' if args.reverse else 'Нет'}")
        print("----------------------")

    # =========================================================================
    # ЭТАП 2: СБОР ДАННЫХ О ЗАВИСИМОСТЯХ ИЗ NUGET РЕПОЗИТОРИЯ
    # =========================================================================
    
    def get_nuget_service_index(self, source_url: str) -> Dict:
        """
        Получение индекс сервиса NuGet - основа Этапа 2
        """
        try:
            req = urllib.request.Request(
                source_url,
                headers={'User-Agent': 'DependencyVisualizer/1.0'}
            )
            
            with urllib.request.urlopen(req, timeout=30) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}: {response.reason}")
                
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
        Поиск базового URL для доступа к пакетам - часть Этапа 2
        """
        for resource in service_index.get('resources', []):
            resource_type = resource.get('@type', '')
            if resource_type.startswith('PackageBaseAddress'):
                return resource['@id']
        
        raise Exception("В индекс сервиса не найден PackageBaseAddress endpoint")
    
    def get_package_versions(self, package_name: str, base_url: str) -> List[str]:
        """
        Получение списка доступных версий пакета - часть Этапа 2
        """
        try:
            package_name_lower = package_name.lower()
            url = f"{base_url}{package_name_lower}/index.json"
            
            with urllib.request.urlopen(url, timeout=30) as response:
                data = json.loads(response.read().decode('utf-8'))
                versions = data.get('versions', [])
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
        Получение NUSpec файла пакета - основной метод Этапа 2
        """
        try:
            package_name_lower = package_name.lower()
            url = f"{base_url}{package_name_lower}/{version}/{package_name_lower}.nuspec"
            
            with urllib.request.urlopen(url, timeout=30) as response:
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
        Парсинг зависимостей из NUSpec XML - ключевая часть Этапа 2
        """
        dependencies = []
        
        try:
            root = ET.fromstring(nuspec_content)
            ns = {'nuspec': 'http://schemas.microsoft.com/packaging/2013/05/nuspec.xsd'}
            
            metadata = root.find('nuspec:metadata', ns)
            if metadata is None:
                return dependencies
            
            dependencies_elem = metadata.find('nuspec:dependencies', ns)
            if dependencies_elem is None:
                return dependencies
            
            for dep_elem in dependencies_elem.findall('nuspec:dependency', ns):
                dep_id = dep_elem.get('id')
                if dep_id and dep_id.strip():
                    dependencies.append(dep_id.strip())
            
        except ET.ParseError as e:
            print(f"Предупреждение: ошибка парсинга XML nuspec: {e}")
        except Exception as e:
            print(f"Предупреждение: ошибка извлечения зависимостей: {e}")
        
        return dependencies

    def get_direct_dependencies(self, package_name: str, version: str) -> List[str]:
        """
        Получение прямых зависимостей пакета - главный результат Этапа 2
        """
        cache_key = f"{package_name}@{version}"
        if cache_key in self.package_cache:
            return self.package_cache[cache_key]
        
        dependencies = []
        
        try:
            service_index = self.get_nuget_service_index(self.config['source'])
            base_url = self.find_package_base_url(service_index)
            
            actual_version = version
            if version == 'latest':
                versions = self.get_package_versions(package_name, base_url)
                if versions:
                    actual_version = versions[-1]
                else:
                    raise Exception(f"Не найдены версии пакета {package_name}")
            
            nuspec_content = self.get_package_nuspec(package_name, actual_version, base_url)
            dependencies = self.parse_dependencies_from_nuspec(nuspec_content)
            
            self.package_cache[cache_key] = dependencies
            
        except Exception as e:
            print(f"Ошибка получения зависимостей для {package_name}: {e}")
        
        return dependencies

    # =========================================================================
    # ЭТАП 3: ОСНОВНЫЕ ОПЕРАЦИИ С ГРАФОМ ЗАВИСИМОСТЕЙ
    # =========================================================================
    
    def load_test_repository(self, file_path: str) -> Dict[str, List[str]]:
        """
        Загрузка тестового репозитория - часть Этапа 3
        """
        graph = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    if not line or line.startswith('#'):
                        continue
                    
                    if ':' in line:
                        package_part, deps_part = line.split(':', 1)
                        package = package_part.strip()
                        
                        dependencies = []
                        if deps_part.strip():
                            for dep in deps_part.split(','):
                                dep_clean = dep.strip()
                                if dep_clean:
                                    dependencies.append(dep_clean)
                        
                        graph[package] = dependencies
                    else:
                        print(f"Предупреждение: строка {line_num} имеет неверный формат: {line}")
                        
        except Exception as e:
            raise Exception(f"Ошибка загрузки тестового репозитория: {e}")
        
        return graph

    def should_filter_package(self, package_name: str) -> bool:
        """
        Проверка фильтрации пакета - часть Этапа 3
        """
        if not self.config.get('filter'):
            return False
        
        return self.config['filter'] in package_name

    def bfs_build_dependency_graph(self, start_package: str, version: str = 'latest', 
                                 path: List[str] = None) -> None:
        """
        Построение графа зависимостей BFS с рекурсией - основа Этапа 3
        """
        if path is None:
            path = []
        
        if start_package in path:
            cycle_path = ' -> '.join(path + [start_package])
            print(f"Обнаружена циклическая зависимость: {cycle_path}")
            self.cycle_detected = True
            return
        
        self.recursion_depth += 1
        if self.recursion_depth > self.max_recursion_depth:
            print(f"Достигнута максимальная глубина рекурсии ({self.max_recursion_depth}) для пакета {start_package}")
            self.recursion_depth -= 1
            return
        
        if start_package in self.visited_packages:
            self.recursion_depth -= 1
            return
        
        self.visited_packages.add(start_package)
        
        dependencies = []
        if self.config.get('test_mode'):
            test_graph = self.load_test_repository(self.config['source'])
            dependencies = test_graph.get(start_package, [])
        else:
            dependencies = self.get_direct_dependencies(start_package, version)
        
        if self.recursion_depth == 1:
            print(f"Прямые зависимости пакета {start_package}:")
            if dependencies:
                for dep in dependencies:
                    print(f"  - {dep}")
            else:
                print("  (нет зависимостей)")
        
        filtered_dependencies = []
        for dep in dependencies:
            if not self.should_filter_package(dep):
                filtered_dependencies.append(dep)
            else:
                print(f"Пакет отфильтрован: {dep}")
        
        self.dependency_graph[start_package] = filtered_dependencies
        
        for dep in filtered_dependencies:
            self.reverse_dependency_graph[dep].append(start_package)
        
        new_path = path + [start_package]
        for dep in filtered_dependencies:
            self.bfs_build_dependency_graph(dep, 'latest', new_path)
        
        self.recursion_depth -= 1

    # =========================================================================
    # ЭТАП 4: ОБРАТНЫЕ ЗАВИСИМОСТИ
    # =========================================================================
    
    def find_reverse_dependencies(self, target_package: str) -> List[str]:
        """
        Поиск обратных зависимостей - основа Этапа 4
        """
        visited = set()
        queue = deque([target_package])
        reverse_deps = []
        
        while queue:
            current_package = queue.popleft()
            
            if current_package in visited:
                continue
                
            visited.add(current_package)
            
            dependents = self.reverse_dependency_graph.get(current_package, [])
            
            for dependent in dependents:
                if dependent not in visited:
                    if dependent != target_package:
                        reverse_deps.append(dependent)
                    queue.append(dependent)
        
        return reverse_deps

    def get_reverse_dependencies_for_package(self, package_name: str) -> List[str]:
        """
        Получение обратных зависимостей для указанного пакета - Этап 4
        """
        if self.config.get('test_mode'):
            test_graph = self.load_test_repository(self.config['source'])
            reverse_deps = []
            
            for pkg, deps in test_graph.items():
                if package_name in deps:
                    reverse_deps.append(pkg)
            
            return reverse_deps
        else:
            return self.find_reverse_dependencies(package_name)

    # =========================================================================
    # ЭТАП 5: ВИЗУАЛИЗАЦИЯ ГРАФА ЗАВИСИМОСТЕЙ (ТОЛЬКО DOT)
    # =========================================================================
    
    def print_ascii_tree(self, start_package: str, visited: Set[str] = None, 
                        prefix: str = "", is_last: bool = True) -> None:
        """
        Вывод ASCII-дерева зависимостей - часть Этапа 5
        """
        if visited is None:
            visited = set()
        
        if start_package in visited:
            connector = "└── " if is_last else "├── "
            print(f"{prefix}{connector}{start_package} (циклическая зависимость)")
            return
        
        visited.add(start_package)
        
        connector = "└── " if is_last else "├── "
        print(f"{prefix}{connector}{start_package}")
        
        dependencies = self.dependency_graph.get(start_package, [])
        
        for i, dep in enumerate(dependencies):
            is_last_dep = (i == len(dependencies) - 1)
            new_prefix = prefix + ("    " if is_last else "│   ")
            self.print_ascii_tree(dep, visited.copy(), new_prefix, is_last_dep)
    
    def generate_graphviz(self) -> str:
        """
        Генерация Graphviz кода - основа Этапа 5
        Создает текстовое представление графа на языке DOT
        """
        lines = []
        
        lines.append('digraph Dependencies {')
        lines.append('    rankdir=TB;')
        lines.append('    node [shape=box, style=filled, fillcolor=lightblue];')
        lines.append('    edge [arrowsize=0.8];')
        lines.append('    graph [fontname="Arial"];')
        lines.append('    node [fontname="Arial"];')
        lines.append('    edge [fontname="Arial"];')
        
        edges_added = set()
        
        for package, dependencies in self.dependency_graph.items():
            if self.should_filter_package(package):
                continue
                
            for dep in dependencies:
                if self.should_filter_package(dep):
                    continue
                    
                edge = f'"{package}" -> "{dep}"'
                if edge not in edges_added:
                    lines.append(f'    {edge};')
                    edges_added.add(edge)
        
        lines.append('}')
        
        return '\n'.join(lines)
    
    def save_dot(self, graphviz_content: str, output_file: str) -> bool:
        """
        Сохранение графа в DOT файл - основа Этапа 5
        Сохраняет только DOT описание без генерации SVG
        """
        try:
            # Гарантируем расширение .dot
            if not output_file.endswith('.dot'):
                dot_file = output_file + '.dot'
            else:
                dot_file = output_file
            
            # Сохраняем DOT файл
            with open(dot_file, 'w', encoding='utf-8') as f:
                f.write(graphviz_content)
            
            print(f"DOT файл сохранен: {dot_file}")
            print("Текстовое представление графа готово для визуализации")
            
            # Создаем инструкцию для онлайн просмотра
            self.create_online_preview(graphviz_content, dot_file)
            
            return True
            
        except Exception as e:
            print(f"Ошибка сохранения DOT файла: {e}")
            return False

    def create_online_preview(self, graphviz_content: str, dot_file: str) -> None:
        """
        Создает HTML файл с инструкцией для онлайн просмотра графа
        """
        import urllib.parse
        
        encoded_dot = urllib.parse.quote(graphviz_content)
        
        html_content = f'''
<!DOCTYPE html>
<html>
<head>
    <title>Graph Preview</title>
    <meta charset="UTF-8">
</head>
<body>
    <h2>Просмотр графа зависимостей</h2>
    
    <h3>Способ 1: Онлайн просмотр</h3>
    <p>1. Перейдите на сайт: <a href="https://dreampuf.github.io/GraphvizOnline/" target="_blank">GraphvizOnline</a></p>
    <p>2. Скопируйте код ниже и вставьте на сайт:</p>
    <textarea rows="15" cols="80" style="font-family: monospace; font-size: 12px;" id="dotCode">
{graphviz_content}
    </textarea>
    <br>
    <button onclick="copyToClipboard()">Скопировать код</button>
    
    <h3>Способ 2: Прямая ссылка</h3>
    <a href="https://dreampuf.github.io/GraphvizOnline/#{encoded_dot}" target="_blank">
        Открыть граф в GraphvizOnline
    </a>
    
    <h3>Способ 3: Локальный файл</h3>
    <p>DOT файл сохранен: <strong>{dot_file}</strong></p>

    <script>
        function copyToClipboard() {{
            const textarea = document.getElementById('dotCode');
            textarea.select();
            document.execCommand('copy');
            alert('Код скопирован! Теперь вставьте его на сайт GraphvizOnline');
        }}
    </script>
</body>
</html>
'''
        
        preview_file = dot_file.replace('.dot', '_preview.html')
        with open(preview_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"Файл для онлайн просмотра создан: {preview_file}")

    # =========================================================================
    # ОСНОВНОЙ МЕТОД ЗАПУСКА ПРИЛОЖЕНИЯ
    # =========================================================================
    
    def run(self) -> None:
        """
        Главный метод запуска - объединяет все 5 этапов
        """
        try:
            print("ЗАПУСК ИНСТРУМЕНТА ВИЗУАЛИЗАЦИИ ЗАВИСИМОСТЕЙ")
            print("============================================")
            
            # ЭТАП 1: КОНФИГУРАЦИЯ
            print("Этап 1: Парсинг и валидация аргументов...")
            args = self.parse_arguments()
            
            errors = self.validate_arguments(args)
            if errors:
                print("Ошибки в параметрах:")
                for error in errors:
                    print(f"  - {error}")
                sys.exit(1)
            
            self.config = vars(args)
            self.print_config(args)
            
            if args.reverse:
                # РЕЖИМ ОБРАТНЫХ ЗАВИСИМОСТЕЙ (ЭТАП 4)
                print(f"\nЭтап 4: Поиск обратных зависимостей для {args.package}")
                
                if args.test_mode:
                    reverse_deps = self.get_reverse_dependencies_for_package(args.package)
                else:
                    print("Построение графа для поиска обратных зависимостей...")
                    self.bfs_build_dependency_graph(args.package, args.version)
                    reverse_deps = self.get_reverse_dependencies_for_package(args.package)
                
                print(f"Пакеты, зависящие от {args.package}:")
                if reverse_deps:
                    for dep in sorted(reverse_deps):
                        print(f"  - {dep}")
                else:
                    print("  (обратные зависимости не найдены)")
                    
            else:
                # ОСНОВНОЙ РЕЖИМ: ПОСТРОЕНИЕ И ВИЗУАЛИЗАЦИЯ ГРАФА
                print(f"\nЭтап 2: Сбор данных о зависимостях {args.package}...")
                
                # ЭТАП 2+3: ПОСТРОЕНИЕ ГРАФА ЗАВИСИМОСТЕЙ
                self.bfs_build_dependency_graph(args.package, args.version)
                
                total_packages = len(self.dependency_graph)
                print(f"\nГраф построен: {total_packages} пакетов")
                
                if self.cycle_detected:
                    print("В графе обнаружены циклические зависимости")
                
                # ЭТАП 5: ВИЗУАЛИЗАЦИЯ (ТОЛЬКО DOT)
                print(f"\nЭтап 5: Визуализация графа...")
                
                if args.ascii_tree:
                    print(f"ASCII-дерево зависимостей:")
                    print("-" * 40)
                    self.print_ascii_tree(args.package)
                    print("-" * 40)
                
                # Graphviz DOT визуализация
                graphviz_content = self.generate_graphviz()
                self.save_dot(graphviz_content, args.output)
            
            print("\nВСЕ ЭТАПЫ ВЫПОЛНЕНЫ УСПЕШНО!")
            print("=============================")
            
        except KeyboardInterrupt:
            print("\nРабота прервана пользователем")
            sys.exit(130)
        except Exception as e:
            print(f"\nКритическая ошибка: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

def create_test_repository() -> str:
    """
    Создание тестового репозитория для демонстрации
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
    Точка входа в приложение
    """
    if len(sys.argv) == 1:
        print("ДЕМОНСТРАЦИОННЫЙ РЕЖИМ")
        print("Создание тестового репозитория...")
        test_file = create_test_repository()
        
        visualizer = DependencyVisualizer()
        
        print("\nТЕСТ 1: Основной режим с ASCII-деревом")
        print("=====================================")
        sys.argv = [
            'dependency_visualizer.py',
            '--package', 'A', 
            '--source', test_file,
            '--test-mode',
            '--ascii-tree',
            '--output', 'test_graph.dot'
        ]
        visualizer.run()
        
        print("\nТЕСТ 2: Режим обратных зависимостей")
        print("==================================")
        sys.argv = [
            'dependency_visualizer.py', 
            '--package', 'A',
            '--source', test_file,
            '--test-mode',
            '--reverse'
        ]
        visualizer.run()
        
        print("\nТЕСТ 3: Фильтрация пакетов (исключить 'Test')")
        print("============================================")
        sys.argv = [
            'dependency_visualizer.py',
            '--package', 'X',
            '--source', test_file, 
            '--test-mode',
            '--filter', 'Test',
            '--ascii-tree'
        ]
        visualizer.run()
        
        try:
            os.remove(test_file)
            print(f"\nТестовый файл удален: {test_file}")
        except:
            pass
            
        print("\nДля работы с реальными пакетами используйте:")
        print('python dependency_visualizer.py --package "Newtonsoft.Json" --source "https://api.nuget.org/v3/index.json"')
        
    else:
        visualizer = DependencyVisualizer()
        visualizer.run()

if __name__ == "__main__":
    main()
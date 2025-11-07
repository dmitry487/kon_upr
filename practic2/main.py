#!/usr/bin/env python3
"""
Инструмент визуализации графа зависимостей для NuGet пакетов
Этап 1: Минимальный прототип с конфигурацией
"""

import argparse
import sys
import os

class DependencyVisualizerStage1:
    def __init__(self):
        self.config = {}
        
    def parse_arguments(self):
        """Парсинг аргументов командной строки"""
        parser = argparse.ArgumentParser(
            description='Визуализатор графа зависимостей для NuGet пакетов - Этап 1',
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        parser.add_argument(
            '--package',
            required=True,
            help='Имя анализируемого пакета'
        )
        
        parser.add_argument(
            '--source',
            required=True,
            help='URL-адрес репозитория или путь к файлу тестового репозитория'
        )
        
        parser.add_argument(
            '--test-mode',
            action='store_true',
            default=False,
            help='Режим работы с тестового репозитория'
        )
        
        parser.add_argument(
            '--version',
            default='latest',
            help='Версия пакета (по умолчанию: latest)'
        )
        
        parser.add_argument(
            '--output',
            default='dependencies.svg',
            help='Имя сгенерированного файла с изображением графа'
        )
        
        parser.add_argument(
            '--ascii-tree',
            action='store_true',
            default=False,
            help='Режим вывода зависимостей в формате ASCII-дерева'
        )
        
        parser.add_argument(
            '--filter',
            default='',
            help='Подстрока для фильтрации пакетов'
        )
        
        return parser.parse_args()
    
    def validate_arguments(self, args):
        """Валидация параметров"""
        errors = []
        
        # Проверка имени пакета
        if not args.package or not args.package.strip():
            errors.append("Имя пакета не может быть пустым")
        
        # Проверка источника
        if not args.source or not args.source.strip():
            errors.append("Источник не может быть пустым")
        
        # В тестовом режиме проверяем существование файла
        if args.test_mode and not os.path.exists(args.source):
            errors.append(f"Тестовый файл не найден: {args.source}")
        
        # Проверка выходного файла
        if args.output:
            output_dir = os.path.dirname(args.output) or '.'
            if not os.path.exists(output_dir):
                try:
                    os.makedirs(output_dir, exist_ok=True)
                except:
                    errors.append(f"Не удается создать директорию для выходного файла: {output_dir}")
        
        return errors
    
    def print_config(self, args):
        """Вывод конфигурации в формате ключ-значение"""
        print("Конфигурация приложения:")
        print("=" * 40)
        print(f"Имя пакета: {args.package}")
        print(f"Источник: {args.source}")
        print(f"Режим тестирования: {'Да' if args.test_mode else 'Нет'}")
        print(f"Версия пакета: {args.version}")
        print(f"Выходной файл: {args.output}")
        print(f"ASCII-дерево: {'Да' if args.ascii_tree else 'Нет'}")
        print(f"Фильтр пакетов: {args.filter if args.filter else 'Не задан'}")
        print("=" * 40)
    
    def run(self):
        """Основной метод запуска приложения"""
        try:
            # Парсинг аргументов
            args = self.parse_arguments()
            
            # Валидация параметров
            errors = self.validate_arguments(args)
            if errors:
                print("Ошибки в параметрах:")
                for error in errors:
                    print(f"  - {error}")
                sys.exit(1)
            
            # Вывод конфигурации (требование этапа 1)
            self.print_config(args)
            
            print("Этап 1 завершен успешно! Приложение настроено с указанными параметрами.")
            
        except Exception as e:
            print(f"Критическая ошибка: {e}")
            sys.exit(1)

def main():
    """Точка входа в приложение"""
    visualizer = DependencyVisualizerStage1()
    visualizer.run()

if __name__ == "__main__":
    main()
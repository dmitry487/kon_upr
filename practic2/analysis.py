#!/usr/bin/env python3
"""
Задача 1: Анализ пакета matplotlib (Python)
"""

def analyze_matplotlib():
    print("=== АНАЛИЗ ПАКЕТА MATPLOTLIB (Python) ===")
    print("\n1. СЛУЖЕБНАЯ ИНФОРМАЦИЯ:")
    
    # Основные элементы служебной информации
    service_info = {
        "Имя пакета": "matplotlib",
        "Тип": "Графическая библиотека",
        "Основное назначение": "Построение графиков и визуализация данных",
        "Версия (пример)": "3.7.0+",
        "Главные модули": [
            "pyplot - интерфейс MATLAB-style",
            "figure - управление фигурами", 
            "axes - система координат",
            "backends - рендеринг (TkAgg, Qt5Agg, etc)"
        ],
        "Ключевые зависимости": [
            "numpy - численные вычисления",
            "pillow - работа с изображениями",
            "cycler - управление стилями",
            "python-dateutil - работа с датами"
        ],
        "Формат пакета": "Wheel (.whl) или Source (.tar.gz)",
        "Стандартные файлы": [
            "setup.py - конфигурация сборки",
            "pyproject.toml - современная конфигурация",
            "PKG-INFO - метаданные пакета",
            "README.md - документация"
        ]
    }
    
    for key, value in service_info.items():
        if isinstance(value, list):
            print(f"{key}:")
            for item in value:
                print(f"  • {item}")
        else:
            print(f"{key}: {value}")
    
    print("\n2. СТРУКТУРА PKG-INFO / setup.py:")
    pkg_info_structure = {
        "Metadata-Version": "Версия формата метаданных",
        "Name": "Имя пакета (matplotlib)",
        "Version": "Версия пакета",
        "Summary": "Краткое описание пакета",
        "Home-page": "URL репозитория",
        "Author": "Автор/организация",
        "Author-email": "Email автора",
        "License": "Тип лицензии",
        "Requires-Python": "Совместимые версии Python",
        "Requires-Dist": "Зависимости пакета"
    }
    
    for field, description in pkg_info_structure.items():
        print(f"  {field}: {description}")
    
    print("\n3. ПОЛУЧЕНИЕ БЕЗ MENЕДЖЕРА ПАКЕТОВ:")
    methods = [
        "Прямая загрузка с PyPI: https://pypi.org/project/matplotlib/#files",
        "GitHub репозиторий: git clone https://github.com/matplotlib/matplotlib",
        "Ручная установка: python setup.py install",
        "Через wheel: pip download matplotlib --no-deps"
    ]
    
    for i, method in enumerate(methods, 1):
        print(f"  {i}. {method}")

def analyze_express():
    print("\n" + "="*60)
    print("=== АНАЛИЗ ПАКЕТА EXPRESS (JavaScript) ===")
    print("\n1. СЛУЖЕБНАЯ ИНФОРМАЦИЯ:")
    
    service_info = {
        "Имя пакета": "express",
        "Тип": "Веб-фреймворк для Node.js",
        "Основное назначение": "Создание веб-приложений и API",
        "Версия (пример)": "4.18.0+",
        "Главные компоненты": [
            "Router - маршрутизация запросов",
            "Middleware - промежуточные обработчики",
            "Template engines - шаблонизаторы",
            "Static files - обслуживание статики"
        ],
        "Ключевые зависимости": [
            "body-parser - парсинг тел запросов",
            "cookie-parser - работа с cookies",
            "debug - отладка",
            "qs - парсинг query строк"
        ],
        "Формат пакета": "Tarball (.tgz) или Git репозиторий",
        "Стандартные файлы": [
            "package.json - метаданные и зависимости",
            "index.js - главный файл",
            "README.md - документация",
            "LICENSE - лицензия"
        ]
    }
    
    for key, value in service_info.items():
        if isinstance(value, list):
            print(f"{key}:")
            for item in value:
                print(f"  • {item}")
        else:
            print(f"{key}: {value}")
    
    print("\n2. СТРУКТУРА package.json:")
    package_json_structure = {
        "name": "Имя пакета (express)",
        "version": "Версия семантического версионирования",
        "description": "Описание пакета",
        "main": "Главный файл (обычно index.js)",
        "scripts": "NPM скрипты для сборки/запуска",
        "keywords": "Ключевые слова для поиска",
        "author": "Автор пакета",
        "license": "Лицензия (MIT)",
        "dependencies": "Производственные зависимости",
        "devDependencies": "Зависимости для разработки",
        "repository": "Ссылка на репозиторий",
        "engines": "Совместимые версии Node.js"
    }
    
    for field, description in package_json_structure.items():
        print(f"  {field}: {description}")
    
    print("\n3. ПОЛУЧЕНИЕ БЕЗ МЕНЕДЖЕРА ПАКЕТОВ:")
    methods = [
        "Прямая загрузка: wget https://registry.npmjs.org/express/-/express-[version].tgz",
        "GitHub: git clone https://github.com/expressjs/express.git",
        "Ручная установка: npm install ./express-directory",
        "Через CDN: https://cdnjs.com/libraries/express"
    ]
    
    for i, method in enumerate(methods, 1):
        print(f"  {i}. {method}")

def main():
    print("АНАЛИЗ СЛУЖЕБНОЙ ИНФОРМАЦИИ ПАКЕТОВ")
    print("=" * 60)
    
    analyze_matplotlib()
    analyze_express()
    
    print("\n" + "=" * 60)
    print("ВЫВОДЫ:")
    print("• Python пакеты используют setup.py/PKG-INFO для метаданных")
    print("• JavaScript пакеты используют package.json для метаданных") 
    print("• Оба можно получить напрямую из репозиториев GitHub")
    print("• PyPI и npm registry предоставляют прямые ссылки для загрузки")

if __name__ == "__main__":
    main()
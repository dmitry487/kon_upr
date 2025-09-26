#!/usr/bin/env python3
"""
Демонстрационный скрипт для этапа 1
"""

from shell_emulator import ShellEmulator

def demo_stage1():
    """Демонстрация работы эмулятора"""
    shell = ShellEmulator("testvfs")
    
    print("=== ДЕМОНСТРАЦИЯ РАБОТЫ ЭМУЛЯТОРА ===\n")
    
    # Тестирование различных сценариев
    test_cases = [
        "ls",
        "ls -l -a",
        'ls "аргумент в кавычках"',
        "cd /home/user",
        "cd",  # Ошибочный случай - cd без аргументов
        "unknown_command",  # Неизвестная команда
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Тест {i}: {test_case}")
        print("-" * 40)
        
        parts = shell.parse_arguments(test_case)
        if parts is None:
            print("ОШИБКА ПАРСИНГА")
        else:
            command = parts[0]
            args = parts[1:]
            shell.execute_command(command, args)
        
        print()
    
    print("Демонстрация завершена. Для интерактивного режима запустите shell_emulator.py")

if __name__ == "__main__":
    demo_stage1()
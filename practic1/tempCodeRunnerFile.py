
import shlex
import sys
import argparse
import os

class ShellEmulator:
    def __init__(self, vfs_name="myvfs", vfs_path=None, script_path=None):
        self.vfs_name = vfs_name
        self.vfs_path = vfs_path
        self.script_path = script_path
        self.current_dir = "/"
        
 
        self.commands = {
            'ls': self.cmd_ls,
            'cd': self.cmd_cd,
            'echo': self.cmd_echo,
            'pwd': self.cmd_pwd,
            'exit': self.cmd_exit
        }
        
     
        print("=== ПАРАМЕТРЫ ЗАПУСКА ЭМУЛЯТОРА ===")
        print(f"Имя VFS: {self.vfs_name}")
        print(f"Путь к VFS: {vfs_path or 'Не указан'}")
        print(f"Стартовый скрипт: {script_path or 'Не указан'}")
        print("=" * 40)
    
    def parse_arguments(self, command_line):
        """Парсер, корректно обрабатывающий аргументы в кавычках (Этап 1)"""
        try:
            return shlex.split(command_line)
        except ValueError as e:
            print(f"Ошибка парсинга: {e}")
            return None
    
    def cmd_ls(self, args):
        """Команда ls - вывод аргументов (Этап 1)"""
        print(f"Команда: ls")
        print(f"Аргументы: {args}")
        print(f"Текущая директория: {self.current_dir}")
        return True
    
    def cmd_cd(self, args):
        """Команда cd - заглушка (Этап 1)"""
        print(f"Команда: cd")
        print(f"Аргументы: {args}")
        if args:
            print(f"Попытка перейти в директорию: {args[0]}")

            if args[0].startswith('/'):
                self.current_dir = args[0]
            else:
                self.current_dir = os.path.join(self.current_dir, args[0])
            return True
        else:
            print("Ошибка: cd требует аргумент")
            return False
    
    def cmd_echo(self, args):
        """Команда echo - вывод аргументов"""
        print(f"Команда: echo")
        print(f"Аргументы: {args}")
        if args:
            print(" ".join(args))
        return True
    
    def cmd_pwd(self, args):
        """Команда pwd - вывод текущей директории"""
        print(f"Команда: pwd")
        print(f"Текущая директория: {self.current_dir}")
        return True
    
    def cmd_exit(self, args):
        """Команда exit - выход из эмулятора (Этап 1)"""
        print("Выход из эмулятора")
        sys.exit(0)
    
    def execute_command(self, command, args):
        """Выполнение команды с обработкой ошибок (Этап 1)"""
        if command in self.commands:
            return self.commands[command](args)
        else:
            print(f"Ошибка: неизвестная команда '{command}'")
            return False
    
    def get_prompt(self):
        """Формирование приглашения с именем VFS (Этап 1)"""
        return f"{self.vfs_name}:{self.current_dir}$ "
    
    def run_script(self, script_path):
        """Выполнение стартового скрипта (Этап 2)"""
        if not os.path.exists(script_path):
            print(f"Ошибка: скрипт '{script_path}' не найден")
            return False
        
        print(f"=== ВЫПОЛНЕНИЕ СКРИПТА: {script_path} ===")
        
        with open(script_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
   
            if not line or line.startswith('#'):
                continue
                
         
            print(f"\n[{line_num}] {self.get_prompt()}{line}")
            
            parts = self.parse_arguments(line)
            if parts is None:
                print("Ошибка: неверный формат команды в скрипте")
                return False
            
            command = parts[0]
            args = parts[1:]
            
          
            if not self.execute_command(command, args):
                print(f"Ошибка выполнения команды в строке {line_num}")
                return False
        
        print("\n=== СКРИПТ УСПЕШНО ВЫПОЛНЕН ===")
        return True
    
    def run_interactive(self):
        """Запуск интерактивного режима (Этап 1)"""
        print("Добро пожаловать в эмулятор командной строки!")
        print("Доступные команды: ls, cd, pwd, echo, exit")
        print("Для выхода введите 'exit' или нажмите Ctrl+D")
        print("-" * 50)
     
        if self.script_path:
            if not self.run_script(self.script_path):
                print("Завершение работы из-за ошибки в скрипте")
                return
            print("\n" + "="*50)
            print("Переход в интерактивный режим...")
            print("="*50)
        

        while True:
            try:
                user_input = input(self.get_prompt()).strip()
                
                if not user_input:
                    continue
                
         
                parts = self.parse_arguments(user_input)
                if parts is None:
                    continue
                
                command = parts[0]
                args = parts[1:]
                
           
                self.execute_command(command, args)
                print()  
                
            except KeyboardInterrupt:
                print("\nДля выхода используйте команду 'exit'")
            except EOFError:
                print("\nВыход")
                break

def main():
    """Основная функция с поддержкой параметров командной строки (Этап 2)"""
    parser = argparse.ArgumentParser(
        description='Эмулятор командной строки UNIX-подобной ОС',
        epilog='Примеры использования:\n'
               '  python3 shell_emulator.py\n'
               '  python3 shell_emulator.py --vfs-path /path/to/vfs --script startup.txt\n'
               '  python3 shell_emulator.py --vfs-name myos --script test_commands.txt'
    )
    
    parser.add_argument('--vfs-path', 
                       help='Путь к физическому расположению VFS')
    parser.add_argument('--script', 
                       help='Путь к стартовому скрипту для выполнения')
    parser.add_argument('--vfs-name', 
                       default='myvfs', 
                       help='Имя VFS (по умолчанию: myvfs)')
    
    args = parser.parse_args()
    

    shell = ShellEmulator(
        vfs_name=args.vfs_name,
        vfs_path=args.vfs_path,
        script_path=args.script
    )
    
    shell.run_interactive()

if __name__ == "__main__":
    main()
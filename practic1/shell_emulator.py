import shlex
import sys

class ShellEmulator:
    def __init__(self, vfs_name="myvfs"):
        self.vfs_name = vfs_name
        self.current_dir = "/"
        self.commands = {
            'ls': self.cmd_ls,
            'cd': self.cmd_cd,
            'exit': self.cmd_exit
        }
    
    def parse_arguments(self, command_line):
        """Парсер, корректно обрабатывающий аргументы в кавычках"""
        try:
            return shlex.split(command_line)
        except ValueError as e:
            print(f"Ошибка парсинга: {e}")
            return None
    
    def cmd_ls(self, args):
        """Команда ls - заглушка"""
        print(f"Команда: ls")
        print(f"Аргументы: {args}")
        print(f"Текущая директория: {self.current_dir}")
    
    def cmd_cd(self, args):
        """Команда cd - заглушка"""
        print(f"Команда: cd")
        print(f"Аргументы: {args}")
        if args:
            print(f"Попытка перейти в директорию: {args[0]}")
        else:
            print("Ошибка: cd требует аргумент")
    
    def cmd_exit(self, args):
        """Команда exit"""
        print("Выход из эмулятора")
        sys.exit(0)
    
    def execute_command(self, command, args):
        """Выполнение команды с обработкой ошибок"""
        if command in self.commands:
            self.commands[command](args)
        else:
            print(f"Ошибка: неизвестная команда '{command}'")
    
    def get_prompt(self):
        """Формирование приглашения к вводу с именем VFS"""
        return f"{self.vfs_name}:{self.current_dir}$ "
    
    def run_interactive(self):
        """Запуск интерактивного режима"""
        print("Добро пожаловать в эмулятор командной строки!")
        print("Доступные команды: ls, cd, exit")
        print("Для выхода введите 'exit'")
        print("-" * 50)
        
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
                
            except KeyboardInterrupt:
                print("\nДля выхода используйте команду 'exit'")
            except EOFError:
                print("\nВыход")
                break

def main():
    """Основная функция"""
    shell = ShellEmulator()
    shell.run_interactive()

if __name__ == "__main__":
    main()
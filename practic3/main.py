import json
import struct
import sys

class UVMAssembler:
    def __init__(self):
        self.commands = {
            'load_const': 11,
            'read_mem': 24,
            'write_mem': 30,
            'abs': 7
        }
        
    def parse_program(self, program_json):
        """Парсинг JSON программы в промежуточное представление"""
        intermediate = []
        
        for cmd in program_json['program']:
            cmd_type = cmd['type']
            fields = {}
            
            if cmd_type == 'load_const':
                fields = {
                    'A': self.commands['load_const'],
                    'B': cmd['constant'],
                    'C': cmd['address']
                }
            elif cmd_type == 'read_mem':
                fields = {
                    'A': self.commands['read_mem'],
                    'B': cmd['result_addr'],
                    'C': cmd['source_addr']
                }
            elif cmd_type == 'write_mem':
                fields = {
                    'A': self.commands['write_mem'],
                    'B': cmd['offset'],
                    'C': cmd['value_addr'],
                    'D': cmd['base_addr']
                }
            elif cmd_type == 'abs':
                fields = {
                    'A': self.commands['abs'],
                    'B': cmd['result_addr'],
                    'C': cmd['source_addr']
                }
            
            intermediate.append({
                'type': cmd_type,
                'fields': fields
            })
        
        return intermediate
    
    def encode_command(self, cmd):
        """Кодирование команды в бинарное представление"""
        fields = cmd['fields']
        cmd_type = cmd['type']
        
        if cmd_type == 'load_const':
            A = fields['A']
            B = fields['B']
            C = fields['C']
            
            value = (A & 0x3F) | ((B & 0x3FFF) << 6) | ((C & 0x7F) << 20)
            return struct.pack('<I', value)
            
        elif cmd_type == 'read_mem' or cmd_type == 'abs':
            A = fields['A']
            B = fields['B']
            C = fields['C']
            
            byte1 = A & 0x3F
            byte2 = ((B & 0x7F) << 1) | ((C >> 6) & 0x01)
            byte3 = C & 0x3F
            return struct.pack('BBB', byte1, byte2, byte3)
            
        elif cmd_type == 'write_mem':
            A = fields['A']
            B = fields['B']
            C = fields['C']
            D = fields['D']
            
            byte1 = A & 0x3F
            byte2 = (B >> 8) & 0x3F
            byte3 = B & 0xFF
            byte4 = ((C & 0x7F) << 1) | ((D >> 6) & 0x01)
            byte5 = D & 0x3F
            return struct.pack('BBBBB', byte1, byte2, byte3, byte4, byte5)
    
    def assemble_to_intermediate(self, input_file, test_mode=False):
        """Ассемблирование в промежуточное представление"""
        with open(input_file, 'r') as f:
            program_json = json.load(f)
        
        intermediate = self.parse_program(program_json)
        
        if test_mode:
            self.print_intermediate(intermediate)
        
        return intermediate
    
    def print_intermediate(self, intermediate):
        """Вывод промежуточного представления в формате полей"""
        print("Промежуточное представление:")
        for i, cmd in enumerate(intermediate):
            print(f"Команда {i}: {cmd['type']}")
            for field, value in cmd['fields'].items():
                print(f"  {field}={value}")
            print()
    
    def assemble_to_binary(self, intermediate, output_file, test_mode=False):
        """Ассемблирование в бинарный файл"""
        binary_data = b''
        
        for cmd in intermediate:
            cmd_binary = self.encode_command(cmd)
            binary_data += cmd_binary
            
            if test_mode:
                print(f"Команда {cmd['type']}: ", end="")
                for byte in cmd_binary:
                    print(f"0x{byte:02X}, ", end="")
                print()
        
        with open(output_file, 'wb') as f:
            f.write(binary_data)
        
        return binary_data

def create_test_program():
    """Создание тестовой программы со всеми командами спецификации"""
    test_program = {
        "program": [
            {
                "type": "load_const",
                "constant": 693,
                "address": 81
            },
            {
                "type": "read_mem",
                "result_addr": 94,
                "source_addr": 29
            },
            {
                "type": "write_mem",
                "offset": 77,
                "value_addr": 5,
                "base_addr": 85
            },
            {
                "type": "abs",
                "result_addr": 86,
                "source_addr": 26
            }
        ]
    }
    
    with open('test_program.json', 'w') as f:
        json.dump(test_program, f, indent=2)
    
    print("Создан тестовый файл test_program.json")

def test_specification():
    """Тестирование команд из спецификации УВМ"""
    assembler = UVMAssembler()
    
    # Тест загрузки константы (A=11, B=693, C=81)
    test_load = {
        "program": [
            {"type": "load_const", "constant": 693, "address": 81}
        ]
    }
    
    print("=== Тест загрузки константы ===")
    intermediate = assembler.parse_program(test_load)
    assembler.print_intermediate(intermediate)
    binary = assembler.encode_command(intermediate[0])
    print("Байтовое представление: ", end="")
    for byte in binary:
        print(f"0x{byte:02X}, ", end="")
    print()
    
    # Тест чтения из памяти (A=24, B=94, C=29)
    test_read = {
        "program": [
            {"type": "read_mem", "result_addr": 94, "source_addr": 29}
        ]
    }
    
    print("\n=== Тест чтения из памяти ===")
    intermediate = assembler.parse_program(test_read)
    assembler.print_intermediate(intermediate)
    binary = assembler.encode_command(intermediate[0])
    print("Байтовое представление: ", end="")
    for byte in binary:
        print(f"0x{byte:02X}, ", end="")
    print()
    
    # Тест записи в память (A=30, B=77, C=5, D=85)
    test_write = {
        "program": [
            {"type": "write_mem", "offset": 77, "value_addr": 5, "base_addr": 85}
        ]
    }
    
    print("\n=== Тест записи в память ===")
    intermediate = assembler.parse_program(test_write)
    assembler.print_intermediate(intermediate)
    binary = assembler.encode_command(intermediate[0])
    print("Байтовое представление: ", end="")
    for byte in binary:
        print(f"0x{byte:02X}, ", end="")
    print()
    
    # Тест операции abs (A=7, B=86, C=26)
    test_abs = {
        "program": [
            {"type": "abs", "result_addr": 86, "source_addr": 26}
        ]
    }
    
    print("\n=== Тест операции abs ===")
    intermediate = assembler.parse_program(test_abs)
    assembler.print_intermediate(intermediate)
    binary = assembler.encode_command(intermediate[0])
    print("Байтовое представление: ", end="")
    for byte in binary:
        print(f"0x{byte:02X}, ", end="")
    print()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Использование: python assembler.py <input_file> <output_file> [--test]")
        print("\nТестирование команд спецификации:")
        test_specification()
        print("\nСоздание тестового файла...")
        create_test_program()
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    test_mode = len(sys.argv) > 3 and sys.argv[3] == '--test'
    
    assembler = UVMAssembler()
    intermediate = assembler.assemble_to_intermediate(input_file, test_mode)
    binary_data = assembler.assemble_to_binary(intermediate, output_file, test_mode)
    
    print(f"Ассемблировано {len(intermediate)} команд")
    print(f"Размер бинарного файла: {len(binary_data)} байт")
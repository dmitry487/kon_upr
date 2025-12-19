#!/usr/bin/env python3
"""
Конфигурационный транслятор
"""

import sys
import re
import json

class ConfigTranslator:
    def __init__(self, operation=None, value=1):
        self.constants = {}
        self.output = {}
        self.operation = operation
        self.value = value
    
    def apply_operation(self, num):
        if not isinstance(num, (int, float)):
            return num
        
        if self.operation == 'add':
            return num + self.value
        elif self.operation == 'subtract':
            return num - self.value
        elif self.operation == 'multiply':
            return num * self.value
        elif self.operation == 'divide':
            if self.value != 0:
                return num / self.value
            return num
        return num
    
    def remove_comments(self, text):
        return re.sub(r'\{\{!--.*?--\}\}', '', text, flags=re.DOTALL)
    
    def parse_simple_value(self, token):
        token = token.strip()
        
        if token == 'true':
            return True
        elif token == 'false':
            return False
        elif token.startswith('q(') and token.endswith(')'):
            return token[2:-1]
        elif re.match(r'^-?\d+\.\d*$', token):
            value = float(token)
            return self.apply_operation(value)
        elif re.match(r'^-?\d+$', token):
            value = int(token)
            return self.apply_operation(value)
        elif token in self.constants:
            return self.constants[token]
        elif re.match(r'^[a-zA-Z][_a-zA-Z0-9]*$', token):
            return token
        return token
    
    def parse_value(self, token):
        token = token.strip()
        
        if token.startswith('!{') and token.endswith('}'):
            expr = token[2:-1].strip()
            return self.evaluate_expression(expr)
        elif token.startswith('[') and token.endswith(']'):
            return self.parse_array(token)
        else:
            return self.parse_simple_value(token)
    
    def parse_array(self, token):
        content = token[1:-1].strip()
        if not content:
            return []
        
        elements = []
        current = ""
        depth = 0
        
        i = 0
        while i < len(content):
            char = content[i]
            
            if char == 'q' and i+1 < len(content) and content[i+1] == '(':
                start = i
                paren_count = 0
                while i < len(content):
                    if content[i] == '(':
                        paren_count += 1
                    elif content[i] == ')':
                        paren_count -= 1
                        if paren_count == 0:
                            break
                    i += 1
                if i < len(content):
                    elements.append(self.parse_value(content[start:i+1]))
                    i += 1
                    continue
            
            if char == '[':
                depth += 1
                current += char
            elif char == ']':
                depth -= 1
                current += char
            elif char == ';' and depth == 0:
                if current.strip():
                    elements.append(self.parse_value(current.strip()))
                current = ""
            else:
                current += char
            
            i += 1
        
        if current.strip():
            elements.append(self.parse_value(current.strip()))
        
        return elements
    
    def evaluate_expression(self, expr):
        for name, val in self.constants.items():
            if isinstance(val, (int, float)):
                expr = re.sub(r'\b' + re.escape(name) + r'\b', str(val), expr)
        
        def process_number(match):
            num_str = match.group(0)
            try:
                if '.' in num_str:
                    num = float(num_str)
                else:
                    num = int(num_str)
                return str(self.apply_operation(num))
            except:
                return num_str
        
        expr = re.sub(r'\b\d+(?:\.\d*)?\b', process_number, expr)
        
        while True:
            match = re.search(r'min\(([^)]+)\)', expr)
            if not match:
                break
            
            min_expr = match.group(0)
            args_str = match.group(1)
            
            args = []
            current = ""
            depth = 0
            
            for char in args_str + ',':
                if char == '(':
                    depth += 1
                    current += char
                elif char == ')':
                    depth -= 1
                    current += char
                elif char == ',' and depth == 0:
                    if current.strip():
                        arg_expr = current.strip()
                        if re.match(r'^-?\d+(?:\.\d*)?$', arg_expr):
                            if '.' in arg_expr:
                                args.append(float(arg_expr))
                            else:
                                args.append(int(arg_expr))
                        elif any(op in arg_expr for op in '+-*/'):
                            try:
                                result = eval(arg_expr)
                                args.append(result)
                            except:
                                args.append(0)
                        else:
                            args.append(0)
                    current = ""
                else:
                    current += char
            
            if current.strip():
                arg_expr = current.strip()
                if re.match(r'^-?\d+(?:\.\d*)?$', arg_expr):
                    if '.' in arg_expr:
                        args.append(float(arg_expr))
                    else:
                        args.append(int(arg_expr))
                elif any(op in arg_expr for op in '+-*/'):
                    try:
                        result = eval(arg_expr)
                        args.append(result)
                    except:
                        args.append(0)
                else:
                    args.append(0)
            
            if args:
                min_val = min(args)
                result_val = self.apply_operation(min_val)
                expr = expr.replace(min_expr, str(result_val))
            else:
                expr = expr.replace(min_expr, '0')
        
        expr = expr.replace(' ', '')
        
        while '*' in expr:
            match = re.search(r'([+-]?\d+(?:\.\d*)?)\*([+-]?\d+(?:\.\d*)?)', expr)
            if not match:
                break
            a = float(match.group(1))
            b = float(match.group(2))
            result = a * b
            expr = expr[:match.start()] + str(result) + expr[match.end():]
        
        while '/' in expr:
            match = re.search(r'([+-]?\d+(?:\.\d*)?)/([+-]?\d+(?:\.\d*)?)', expr)
            if not match:
                break
            a = float(match.group(1))
            b = float(match.group(2))
            if b != 0:
                result = a / b
            else:
                result = float('inf')
            expr = expr[:match.start()] + str(result) + expr[match.end():]
        
        i = 0
        while i < len(expr):
            if i > 0 and expr[i] in '+-' and expr[i-1] not in 'eE':
                j = i - 1
                while j >= 0 and (expr[j].isdigit() or expr[j] == '.' or (expr[j] == '-' and j == 0)):
                    j -= 1
                left_str = expr[j+1:i]
                
                k = i + 1
                while k < len(expr) and (expr[k].isdigit() or expr[k] == '.' or (k == i+1 and expr[k] == '-')):
                    k += 1
                right_str = expr[i+1:k]
                
                try:
                    left = float(left_str)
                    right = float(right_str)
                    
                    if expr[i] == '+':
                        result = left + right
                    else:
                        result = left - right
                    
                    expr = expr[:j+1] + str(result) + expr[k:]
                    i = j + len(str(result))
                except:
                    i += 1
            else:
                i += 1
        
        try:
            result = float(expr)
            return int(result) if result.is_integer() else result
        except:
            if re.match(r'^-?\d+(?:\.\d*)?$', expr):
                value = float(expr)
                return self.apply_operation(value)
            return expr
    
    def translate(self, text):
        text = self.remove_comments(text)
        lines = text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            if '->' in line and '=' not in line:
                parts = line.split('->', 1)
                if len(parts) == 2:
                    value_str, name = parts[0].strip(), parts[1].strip()
                    if re.match(r'^[a-zA-Z][_a-zA-Z0-9]*$', name):
                        try:
                            self.constants[name] = self.parse_value(value_str)
                        except:
                            pass
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            if '->' in line:
                parts = line.split('->', 1)
                if len(parts) == 2:
                    value_str, name = parts[0].strip(), parts[1].strip()
                    if re.match(r'^[a-zA-Z][_a-zA-Z0-9]*$', name):
                        self.output[name] = self.parse_value(value_str)
            elif '=' in line:
                parts = line.split('=', 1)
                if len(parts) == 2:
                    name, value_str = parts[0].strip(), parts[1].strip()
                    if re.match(r'^[a-zA-Z][_a-zA-Z0-9]*$', name):
                        self.output[name] = self.parse_value(value_str)
        
        return self.dict_to_toml(self.output)
    
    def dict_to_toml(self, data):
        lines = []
        for key, value in data.items():
            if isinstance(value, str):
                lines.append(f'{key} = "{value}"')
            elif isinstance(value, bool):
                lines.append(f'{key} = {str(value).lower()}')
            elif isinstance(value, list):
                if all(isinstance(x, (int, float)) for x in value):
                    lines.append(f'{key} = [{", ".join(str(x) for x in value)}]')
                elif all(isinstance(x, str) for x in value):
                    lines.append(f'{key} = [{", ".join(json.dumps(x) for x in value)}]')
                elif all(isinstance(x, bool) for x in value):
                    lines.append(f'{key} = [{", ".join(str(x).lower() for x in value)}]')
                else:
                    str_vals = []
                    for x in value:
                        if isinstance(x, str):
                            str_vals.append(json.dumps(x))
                        elif isinstance(x, bool):
                            str_vals.append(str(x).lower())
                        else:
                            str_vals.append(str(x))
                    lines.append(f'{key} = [{", ".join(str_vals)}]')
            else:
                lines.append(f'{key} = {value}')
        return '\n'.join(lines)


def main():
    # Парсим аргументы командной строки
    operation = None
    value = 1
    show_examples_only = True
    
    # Проверяем есть ли аргументы операций
    for i in range(1, len(sys.argv)):
        if sys.argv[i] == '--multiply' and i+1 < len(sys.argv):
            operation = 'multiply'
            value = float(sys.argv[i+1])
            show_examples_only = False
        elif sys.argv[i] == '--add' and i+1 < len(sys.argv):
            operation = 'add'
            value = float(sys.argv[i+1])
            show_examples_only = False
        elif sys.argv[i] == '--subtract' and i+1 < len(sys.argv):
            operation = 'subtract'
            value = float(sys.argv[i+1])
            show_examples_only = False
        elif sys.argv[i] == '--divide' and i+1 < len(sys.argv):
            operation = 'divide'
            value = float(sys.argv[i+1])
            show_examples_only = False
    
    # Примеры конфигураций
    example1 = """{{!-- Конфигурация веб-сервера --}}
8080 -> port
q(localhost) -> host
[q(/api); q(/static)] -> routes
max = !{min(1000, port * 2)}"""
    
    example2 = """{{!-- Настройки игры --}}
100 -> health
50 -> mana
[q(sword); q(potion); 3] -> items
damage = !{health / 2}"""
    
    # Если не указана операция - показываем как использовать
    if show_examples_only:
        print("Пример 1: Веб-сервер")
        print("-" * 40)
        print("До:")
        print(example1)
        print("\nПосле (без операций):")
        t1 = ConfigTranslator()
        print(t1.translate(example1))
        
        print("\n" + "=" * 60)
        
        print("Пример 2: Игра")
        print("-" * 40)
        print("До:")
        print(example2)
        print("\nПосле (без операций):")
        t2 = ConfigTranslator()
        print(t2.translate(example2))
        
        print("\n" + "=" * 60)
        print("Использование с операциями:")
        print("python3 homework/main.py --multiply 5")
        print("python3 homework/main.py --add 50")
        print("python3 homework/main.py --divide 2")
        print("python3 homework/main.py --subtract 10")
        return
    
    # Если указана операция - применяем её к примерам
    print(f"Применяем операцию: {operation} {value}")
    print("=" * 60)
    
    print("\nПример 1: Веб-сервер")
    print("-" * 40)
    print("До:")
    print(example1)
    print(f"\nПосле ({operation} {value}):")
    t1 = ConfigTranslator(operation, value)
    print(t1.translate(example1))
    
    print("\n" + "=" * 60)
    
    print("\nПример 2: Игра")
    print("-" * 40)
    print("До:")
    print(example2)
    print(f"\nПосле ({operation} {value}):")
    t2 = ConfigTranslator(operation, value)
    print(t2.translate(example2))


if __name__ == "__main__":
    main()
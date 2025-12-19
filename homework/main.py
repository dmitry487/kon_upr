import sys
import argparse
import re
import json

class ConfigTranslator:
    """Транслятор учебного конфигурационного языка в TOML"""
    
    def __init__(self):
        self.constants = {}
        self.output = {}
    
    def remove_comments(self, text):
        """Удаление многострочных комментариев {{!-- ... --}}"""
        return re.sub(r'\{\{!--.*?--\}\}', '', text, flags=re.DOTALL)
    
    def parse_simple_value(self, token):
        """Парсинг простого значения (без выражений)"""
        token = token.strip()
        
        # Булевые значения
        if token == 'true':
            return True
        elif token == 'false':
            return False
        
        # Строка q(текст)
        elif token.startswith('q(') and token.endswith(')'):
            return token[2:-1]
        
        # Число
        elif re.match(r'^-?\d+\.\d*$', token):
            return float(token)
        elif re.match(r'^-?\d+$', token):
            return int(token)
        
        # Константа
        elif token in self.constants:
            return self.constants[token]
        
        # Идентификатор
        elif re.match(r'^[a-zA-Z][_a-zA-Z0-9]*$', token):
            # Пробуем вычислить как выражение из одного идентификатора
            if token in self.constants:
                return self.constants[token]
            else:
                # Если это не константа, то это часть выражения
                # Возвращаем как строку для дальнейшей обработки
                return token
        
        return token
    
    def parse_value(self, token):
        """Парсинг значения любого типа"""
        token = token.strip()
        
        # Выражение !{...}
        if token.startswith('!{') and token.endswith('}'):
            expr = token[2:-1].strip()
            return self.evaluate_expression(expr)
        
        # Массив [значение; значение; ...]
        elif token.startswith('[') and token.endswith(']'):
            return self.parse_array(token)
        
        # Простое значение
        else:
            return self.parse_simple_value(token)
    
    def parse_array(self, token):
        """Парсинг массива"""
        content = token[1:-1].strip()
        if not content:
            return []
        
        elements = []
        current = ""
        depth = 0
        in_string = False
        
        for char in content:
            if char == 'q' and not in_string and len(content) > content.index(char) + 1 and content[content.index(char)+1] == '(':
                in_string = True
                current += char
            elif char == ')' and in_string:
                in_string = False
                current += char
            elif char == '[' and not in_string:
                depth += 1
                current += char
            elif char == ']' and not in_string:
                depth -= 1
                current += char
            elif char == ';' and depth == 0 and not in_string:
                if current.strip():
                    elements.append(self.parse_value(current.strip()))
                current = ""
            else:
                current += char
        
        if current.strip():
            elements.append(self.parse_value(current.strip()))
        
        return elements
    
    def evaluate_expression(self, expr):
        """Вычисление выражения !{...}"""
        # Сначала заменяем все константы в выражении
        for name, value in sorted(self.constants.items(), key=lambda x: -len(x[0])):
            if isinstance(value, (int, float)):
                expr = expr.replace(name, str(value))
        
        # Вычисляем выражение
        return self.evaluate_math_expression(expr)
    
    def evaluate_math_expression(self, expr):
        """Вычисление математического выражения"""
        expr = expr.strip()
        
        # Обработка функции min()
        if expr.startswith('min(') and expr.endswith(')'):
            args_str = expr[4:-1]
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
                        # Вычисляем каждый аргумент
                        arg_value = self.evaluate_math_expression(current.strip())
                        args.append(arg_value)
                    current = ""
                else:
                    current += char
            
            if current.strip():
                arg_value = self.evaluate_math_expression(current.strip())
                args.append(arg_value)
            
            return min(args) if args else 0
        
        # Вычисление арифметических операций
        expr = expr.replace(' ', '')
        
        # Сначала вычисляем умножение
        while '*' in expr:
            # Находим умножение
            parts = expr.split('*', 1)
            
            # Находим левый операнд
            left_expr = parts[0]
            i = len(left_expr) - 1
            while i >= 0 and (left_expr[i].isdigit() or left_expr[i] == '.' or left_expr[i] == '-'):
                i -= 1
            
            left_part = left_expr[:i+1]
            left_num = left_expr[i+1:]
            
            # Находим правый операнд
            right_expr = parts[1]
            j = 0
            while j < len(right_expr) and (right_expr[j].isdigit() or right_expr[j] == '.' or 
                                          (j == 0 and right_expr[j] == '-')):
                j += 1
            
            right_num = right_expr[:j]
            right_part = right_expr[j:]
            
            # Вычисляем
            try:
                result = float(left_num) * float(right_num)
                expr = left_part + str(result) + right_part
            except:
                # Если не число, то оставляем как есть
                break
        
        # Затем сложение и вычитание
        # Простой парсинг: ищем + или - не в начале
        i = 1
        while i < len(expr):
            if expr[i] in '+-' and not expr[i-1] in 'eE':
                # Разделяем
                left = expr[:i]
                op = expr[i]
                right = expr[i+1:]
                
                try:
                    left_val = float(left)
                    right_val = float(right)
                    
                    if op == '+':
                        result = left_val + right_val
                    else:
                        result = left_val - right_val
                    
                    expr = str(result)
                    i = 0  # Начинаем заново
                except:
                    i += 1
            else:
                i += 1
        
        # Преобразуем результат
        try:
            result = float(expr)
            return int(result) if result.is_integer() else result
        except:
            # Если это не число, проверяем булевые значения
            if expr == 'true':
                return True
            elif expr == 'false':
                return False
            
            # Пробуем вычислить как выражение с константами
            # Заменяем оставшиеся константы
            for name, value in self.constants.items():
                if isinstance(value, (int, float)):
                    expr = expr.replace(name, str(value))
            
            # Пробуем снова
            try:
                # Простая оценка выражения с помощью eval (осторожно!)
                # Только для безопасных математических выражений
                if all(c in '0123456789+-*/.() ' for c in expr):
                    result = eval(expr)
                    return int(result) if isinstance(result, float) and result.is_integer() else result
                else:
                    # Если содержит небезопасные символы, возвращаем как строку
                    return expr
            except:
                return expr
    
    def translate(self, text):
        """Основной метод трансляции"""
        # Удаляем комментарии
        text = self.remove_comments(text)
        
        lines = text.strip().split('\n')
        
        # Первый проход: собираем все константы
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            if '->' in line:
                parts = line.split('->', 1)
                if len(parts) == 2:
                    value_str, name = parts[0].strip(), parts[1].strip()
                    
                    if re.match(r'^[a-zA-Z][_a-zA-Z0-9]*$', name):
                        try:
                            # Для констант парсим как простое значение (без выражений с другими константами)
                            if value_str.startswith('!{'):
                                # Выражение в константе - вычисляем сразу
                                expr = value_str[2:-1].strip()
                                value = self.evaluate_math_expression(expr)
                            else:
                                value = self.parse_simple_value(value_str)
                            
                            self.constants[name] = value
                        except:
                            # Если не удалось вычислить, оставляем как есть
                            pass
        
        # Второй проход: обрабатываем все строки
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            try:
                # Объявление константы: значение -> имя
                if '->' in line:
                    parts = line.split('->', 1)
                    if len(parts) != 2:
                        continue
                    
                    value_str, name = parts[0].strip(), parts[1].strip()
                    
                    if not re.match(r'^[a-zA-Z][_a-zA-Z0-9]*$', name):
                        continue
                    
                    # Уже обработали в первом проходе, просто добавляем в вывод
                    if name in self.constants:
                        self.output[name] = self.constants[name]
                    else:
                        value = self.parse_value(value_str)
                        self.constants[name] = value
                        self.output[name] = value
                
                # Присваивание: имя = значение
                elif '=' in line:
                    parts = line.split('=', 1)
                    if len(parts) != 2:
                        continue
                    
                    name, value_str = parts[0].strip(), parts[1].strip()
                    
                    if not re.match(r'^[a-zA-Z][_a-zA-Z0-9]*$', name):
                        continue
                    
                    value = self.parse_value(value_str)
                    self.output[name] = value
                
            except Exception as e:
                # Пропускаем ошибки для демо
                print(f"⚠️  Внимание в строке {line_num}: {e}")
                continue
        
        return self.dict_to_toml(self.output)
    
    def dict_to_toml(self, data):
        """Преобразование словаря в TOML"""
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
                    # Смешанный массив
                    str_values = []
                    for x in value:
                        if isinstance(x, str):
                            str_values.append(json.dumps(x))
                        elif isinstance(x, bool):
                            str_values.append(str(x).lower())
                        else:
                            str_values.append(str(x))
                    lines.append(f'{key} = [{", ".join(str_values)}]')
            elif value is None:
                lines.append(f'{key} = null')
            else:
                lines.append(f'{key} = {value}')
        
        return '\n'.join(lines)




def run_demo():
    """Запуск демонстрации"""

    print("КОНФИГУРАЦИОННЫЙ ТРАНСЛЯТОР")

    
    # ПРИМЕР 1: Веб-сервер
    print("\n ПРИМЕР 1: Конфигурация веб-сервера")

    
    web_config = """{{!-- Конфигурация веб-сервера --}}
8080 -> port
q(localhost) -> host
[q(/api); q(/static); q(/admin)] -> routes
ssl_enabled = true
max_connections = !{min(1000, port * 2)}
timeout = !{min(30, max_connections / 50)}"""
    
    print("Входной конфиг:")
    print(web_config)
    print("\n" + "-" * 70)
    
    translator = ConfigTranslator()
    result = translator.translate(web_config)
    
    print("Результат (TOML):")
    print(result)
    
    # ПРИМЕР 2: Игра
    print("\n ПРИМЕР 2: Конфигурация игры")

    
    game_config = """{{!-- Настройки игры --}}
100 -> player_health
50 -> mana
10 -> strength
[q(sword); q(potion); q(shield)] -> inventory
debug_mode = false
sound_enabled = true
damage = !{strength * 2}
max_enemies = !{min(50, player_health / 2)}
difficulty = 1.5
bonus_damage = !{damage * difficulty}"""
    
    print("Входной конфиг:")
    print(game_config)
    print("\n" + "-" * 70)
    
    translator2 = ConfigTranslator()
    result2 = translator2.translate(game_config)
    
    print("Результат (TOML):")
    print(result2)
    
    # ПРИМЕР 3: Все типы данных
    print("\n ПРИМЕР 3: Все типы данных")
    print("-" * 70)
    
    test_config = """5 -> five
10 -> ten
enabled = true
disabled = false
message = q(Hello World!)
sum = !{five + ten}
product = !{five * ten}
minimum = !{min(five, ten, 3)}
mixed_array = [1; !{five}; q(test); true; false; !{ten / 2}; 3.14]"""
    
    print("Входной конфиг:")
    print(test_config)

    translator3 = ConfigTranslator()
    result3 = translator3.translate(test_config)
    
    print("Результат (TOML):")
    print(result3)
    

    
   


def main():
    """Основная функция для командной строки"""
    parser = argparse.ArgumentParser(description='Транслятор конфигурационного языка в TOML')
    parser.add_argument('-o', '--output', required=True, help='Выходной TOML файл')
    
    # Если нет аргументов - запускаем демо
    if len(sys.argv) == 1:
        run_demo()
        return
    
    args = parser.parse_args()
    
    try:
        # Чтение из stdin
        input_text = sys.stdin.read()
        
        if not input_text.strip():
            print("Ошибка: пустой ввод", file=sys.stderr)
            sys.exit(1)
        
        # Трансляция
        translator = ConfigTranslator()
        toml_output = translator.translate(input_text)
        
        # Запись в файл
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(toml_output)
        
        print(f" Успешно! Результат в {args.output}")
        
    except Exception as e:
        print(f" Ошибка: {e}", file=sys.stderr)
        sys.exit(1)




def run_tests():
    """Встроенные тесты"""
    print(" ЗАПУСК ТЕСТОВ")
    print("=" * 70)
    
    tests = [
        ("Числа", "42 -> answer", ["answer = 42"]),
        ("Булевые", "enabled = true", ["enabled = true"]),
        ("Строки", 'q(Hello) -> greeting', ['greeting = "Hello"']),
        ("Массивы", "[1; 2; 3] -> numbers", ["numbers = [1, 2, 3]"]),
        ("Сложение", "5 -> a\n3 -> b\nsum = !{a + b}", ["sum = 8"]),
        ("Умножение", "6 -> m\nn = !{m * 7}", ["n = 42"]),
        ("Min", "val = !{min(10, 5, 8)}", ["val = 5"]),
        ("Комплексный", "10 -> x\ny = !{min(20, x * 3)}", ["y = 20"]),
    ]
    
    passed = 0
    failed = 0
    
    for name, input_text, expected in tests:
        try:
            translator = ConfigTranslator()
            result = translator.translate(input_text)
            
            success = all(e in result for e in expected)
            if success:
                print(f" {name}")
                passed += 1
            else:
                print(f" {name}")
                print(f"   Ожидалось: {expected}")
                print(f"   Получено: {result}")
                failed += 1
                
        except Exception as e:
            print(f" {name} - ошибка: {e}")
            failed += 1
    
    print(f"\n Итог: {passed} пройдено, {failed} упало")
    print("=" * 70)
    
    return failed == 0



if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        success = run_tests()
        sys.exit(0 if success else 1)
    elif len(sys.argv) == 1:
        run_demo()
    else:
        main()
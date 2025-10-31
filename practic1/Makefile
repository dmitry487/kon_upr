# Makefile для shell_emulator.py

.PHONY: help run run-with-script clean test install all

# Директории и файлы
SRCDIR          := src
OUTPUTDIR       := output
SHELL_EMU       := $(SRCDIR)/shell_emulator.py
TEST_SCRIPT     ?= startup.txt

# Установка зависимостей
install:
	@echo "Установка зависимостей..."
	pip install -r requirements.txt

# Запуск в интерактивном режиме
run:
	python3 $(SHELL_EMU)

# Запуск с тестовым скриптом
run-with-script: $(TEST_SCRIPT)
	python3 $(SHELL_EMU) --script $(TEST_SCRIPT)

# Алиасы
test: run-with-script
all: run

# Проверка наличия тестового скрипта
$(TEST_SCRIPT):
	@echo "Ошибка: файл '$(TEST_SCRIPT)' не найден."
	@echo "Создайте его или укажите другой через переменную:"
	@echo "  make run-with-script TEST_SCRIPT=ваш_файл.txt"
	@false

# Очистка
clean:
	@echo "Очистка выходных и временных файлов..."
	rm -f *.pyc
	rm -rf __pycache__
	rm -rf $(OUTPUTDIR)

# Справка
help:
	@echo "Использование:"
	@echo "  make run                     — запустить эмулятор в интерактивном режиме"
	@echo "  make run-with-script         — запустить с тестовым скриптом '$(TEST_SCRIPT)'"
	@echo "  make test                    — аналог run-with-script"
	@echo "  make install                 — установить зависимости из requirements.txt"
	@echo "  make clean                   — удалить временные и выходные файлы"
	@echo "  make all                     — запустить эмулятор (синоним make run)"
	@echo ""
	@echo "Примеры:"
	@echo "  make run"
	@echo "  make run-with-script TEST_SCRIPT=my_commands.txt"
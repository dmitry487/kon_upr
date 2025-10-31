import argparse
import sys
import os
from repository_parser import get_direct_dependencies


def validate_args(args):
    errors = []

    if not args.package:
        errors.append("Имя пакета (--package) обязательно.")
    elif not args.package.replace("-", "").replace("_", "").replace(".", "").isalnum():
        errors.append("Недопустимое имя пакета.")

    if not args.repo:
        errors.append("URL или путь к репозиторию (--repo) обязателен.")

    if args.repo_mode not in ("online", "offline"):
        errors.append("Режим репозитория (--repo-mode) должен быть 'online' или 'offline'.")

    if not args.version:
        errors.append("Версия пакета (--version) обязательна.")
    elif not all(c.isalnum() or c in ".-+" for c in args.version):
        errors.append("Некорректный формат версии пакета.")

    if not args.output:
        errors.append("Имя выходного файла (--output) обязательно.")
    elif not args.output.endswith(('.png', '.svg', '.pdf')):
        errors.append("Поддерживаются только расширения: .png, .svg, .pdf")

    if args.filter and not args.filter.strip():
        errors.append("Фильтр не может быть пустой строкой.")

    if args.repo_mode == "offline":
        errors.append("Режим 'offline' не поддерживается на этапе 2 (только online).")

    if errors:
        for err in errors:
            print(f"Ошибка: {err}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Инструмент визуализации графа зависимостей для NuGet-пакетов."
    )

    parser.add_argument("--package", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--repo-mode", required=True, choices=["online", "offline"])
    parser.add_argument("--version", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--ascii-tree", action="store_true")
    parser.add_argument("--filter", default="")

    args = parser.parse_args()
    validate_args(args)

    # Этап 1: вывод параметров
    print("Настройки приложения:")
    print(f"  package      = {args.package}")
    print(f"  repo         = {args.repo}")
    print(f"  repo-mode    = {args.repo_mode}")
    print(f"  version      = {args.version}")
    print(f"  output       = {args.output}")
    print(f"  ascii-tree   = {args.ascii_tree}")
    print(f"  filter       = {args.filter if args.filter else '(не задан)'}")

    # Этап 2: сбор данных (только online)
    if args.repo_mode == "online":
        try:
            print(f"\n[Этап 2] Получение зависимостей для {args.package} версии {args.version}...")
            dependencies = get_direct_dependencies(args.package, args.version, args.repo)

            if not dependencies:
                print("Прямые зависимости не найдены.")
            else:
                print("Прямые зависимости:")
                for dep_id, dep_version in dependencies:
                    if args.filter and args.filter not in dep_id:
                        continue
                    print(f"  - {dep_id} ({dep_version})")

        except Exception as e:
            print(f"Ошибка при получении зависимостей: {e}", file=sys.stderr)
            sys.exit(1)

    print("\nЭтап 2 завершён.")


if __name__ == "__main__":
    main()
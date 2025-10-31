import sys

# Автоматически подставляем параметры (как будто ты их ввёл)
sys.argv = [
    "main.py",
    "--package", "Newtonsoft.Json",
    "--repo", "https://api.nuget.org/v3-flatcontainer",
    "--repo-mode", "online",
    "--version", "13.0.3",
    "--output", "graph.png"
]

# Теперь подключаем настоящую логику
from repository_parser import get_direct_dependencies

def main():
    package = "Newtonsoft.Json"
    version = "13.0.3"
    repo = "https://api.nuget.org/v3-flatcontainer"

    print("🔍 Получаем зависимости для", package, version)
    try:
        deps = get_direct_dependencies(package, version, repo)
        print("✅ Зависимости:")
        for name, ver in deps:
            print(f"  - {name} ({ver})")
    except Exception as e:
        print("❌ Ошибка:", e)

if __name__ == "__main__":
    main()
import urllib.request
import urllib.parse
import zipfile
import io
import xml.etree.ElementTree as ET
import os
from typing import List, Tuple, Optional


def fetch_nuspec_content(package: str, version: str, repo_url: str) -> str:
    """
    Загружает .nuspec файл пакета из NuGet-репозитория.
    Формат URL: https://api.nuget.org/v3-flatcontainer/{id}/{version}/{id}.nuspec
    """
    # Приводим имя пакета к нижнему регистру (NuGet case-insensitive)
    package_lower = package.lower()
    encoded_package = urllib.parse.quote(package_lower)
    encoded_version = urllib.parse.quote(version)

    nuspec_url = f"{repo_url.rstrip('/')}/{encoded_package}/{encoded_version}/{encoded_package}.nuspec"

    try:
        with urllib.request.urlopen(nuspec_url) as response:
            if response.status == 200:
                return response.read().decode('utf-8')
            else:
                raise RuntimeError(f"HTTP {response.status}: не удалось загрузить .nuspec")
    except Exception as e:
        raise RuntimeError(f"Ошибка при загрузке .nuspec: {e}")


def parse_dependencies_from_nuspec(nuspec_content: str) -> List[Tuple[str, str]]:
    """
    Извлекает прямые зависимости из .nuspec XML.
    Возвращает список кортежей (dependency_id, version_range).
    """
    try:
        root = ET.fromstring(nuspec_content)

        # Пространство имён по умолчанию
        ns = {'ns': 'http://schemas.microsoft.com/packaging/2013/05/nuspec.xsd'}

        dependencies = []
        # Ищем все группы зависимостей (обычно одна для netX.Y)
        dep_groups = root.findall(".//ns:dependencies/ns:group", ns)
        if not dep_groups:
            # Возможно, зависимости указаны без групп
            dep_groups = [root.find(".//ns:dependencies", ns)]

        for group in dep_groups:
            if group is None:
                continue
            for dep in group.findall("ns:dependency", ns):
                dep_id = dep.get("id")
                version = dep.get("version", "*")
                if dep_id:
                    dependencies.append((dep_id, version))

        return dependencies
    except ET.ParseError as e:
        raise RuntimeError(f"Ошибка разбора XML: {e}")


def get_direct_dependencies(package: str, version: str, repo_url: str) -> List[Tuple[str, str]]:
    """
    Получает прямые зависимости пакета из NuGet-репозитория.
    """
    nuspec_content = fetch_nuspec_content(package, version, repo_url)
    deps = parse_dependencies_from_nuspec(nuspec_content)
    return deps
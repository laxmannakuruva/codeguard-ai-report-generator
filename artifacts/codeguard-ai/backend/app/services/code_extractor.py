import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

IGNORED_DIRECTORIES = {
    ".git",
    ".hg",
    ".idea",
    ".next",
    ".pytest_cache",
    ".svn",
    ".venv",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "target",
    "venv",
}

TEXT_EXTENSIONS = {
    ".c",
    ".cc",
    ".cpp",
    ".cs",
    ".css",
    ".go",
    ".gradle",
    ".html",
    ".java",
    ".js",
    ".jsx",
    ".json",
    ".kt",
    ".md",
    ".php",
    ".py",
    ".rb",
    ".rs",
    ".scss",
    ".sh",
    ".sql",
    ".swift",
    ".ts",
    ".tsx",
    ".toml",
    ".txt",
    ".vue",
    ".xml",
    ".yaml",
    ".yml",
}

SPECIAL_TEXT_FILES = {
    "Dockerfile",
    "Gemfile",
    "Makefile",
    "Procfile",
    "go.mod",
    "pom.xml",
    "requirements.txt",
}

MAX_TEXT_FILE_BYTES = 1_000_000


def is_ignored_path(path: Path, root: Path) -> bool:
    try:
        relative_parts = path.relative_to(root).parts
    except ValueError:
        return True
    return any(part in IGNORED_DIRECTORIES for part in relative_parts)


@lru_cache(maxsize=8)
def iter_project_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if path.is_file() and not is_ignored_path(path, root):
            files.append(path)
    return sorted(files, key=lambda item: item.relative_to(root).as_posix().lower())


def relative_path(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


@lru_cache(maxsize=512)
def read_text_file(path: Path) -> str:
    if path.name not in SPECIAL_TEXT_FILES and path.suffix.lower() not in TEXT_EXTENSIONS:
        return ""
    try:
        if path.stat().st_size > MAX_TEXT_FILE_BYTES:
            return ""
        raw = path.read_bytes()
        if b"\x00" in raw:
            return ""
        return raw.decode("utf-8", errors="replace")
    except (OSError, UnicodeError):
        return ""


def read_first_matching(root: Path, names: set[str]) -> tuple[str, str]:
    for path in iter_project_files(root):
        if path.name.lower() in {name.lower() for name in names}:
            text = read_text_file(path)
            if text:
                return relative_path(path, root), text
    return "", ""


def load_json_file(path: Path) -> dict[str, Any]:
    text = read_text_file(path)
    if not text:
        return {}
    try:
        value = json.loads(text)
        return value if isinstance(value, dict) else {}
    except json.JSONDecodeError:
        return {}


def load_json_manifests(root: Path) -> list[tuple[str, dict[str, Any]]]:
    manifests: list[tuple[str, dict[str, Any]]] = []
    for path in iter_project_files(root):
        if path.name in {"package.json", "composer.json"}:
            data = load_json_file(path)
            if data:
                manifests.append((relative_path(path, root), data))
    return manifests


def dependency_names(root: Path) -> set[str]:
    names: set[str] = set()
    for _, manifest in load_json_manifests(root):
        for key in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies", "require"):
            values = manifest.get(key, {})
            if isinstance(values, dict):
                names.update(str(name) for name in values)

    requirements_path = next(
        (path for path in iter_project_files(root) if path.name.lower() in {"requirements.txt", "requirements-dev.txt"}),
        None,
    )
    if requirements_path:
        for line in read_text_file(requirements_path).splitlines():
            candidate = line.strip()
            if candidate and not candidate.startswith(("#", "-")):
                names.add(re.split(r"[<>=!~;\[\s]", candidate, maxsplit=1)[0].lower())

    pyproject_path = next((path for path in iter_project_files(root) if path.name == "pyproject.toml"), None)
    if pyproject_path:
        for line in read_text_file(pyproject_path).splitlines():
            if "dependencies" in line or "requires" in line:
                continue
            match = re.search(r'["\']([A-Za-z0-9_.-]+)(?:[<>=!~\[]|["\'])', line)
            if match:
                names.add(match.group(1).lower())

    for path in iter_project_files(root):
        if path.name in {"Cargo.toml", "go.mod", "pom.xml", "build.gradle", "build.gradle.kts"}:
            text = read_text_file(path)
            names.update(re.findall(r"\b(?:spring-boot|actix-web|tokio|serde|gin-gonic|junit|jpa|laravel|rails)\b", text, re.IGNORECASE))
    return {name for name in names if name}
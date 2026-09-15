import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from ..models.project import ProjectProfile
from .code_extractor import (
    dependency_names,
    iter_project_files,
    load_json_manifests,
    read_text_file,
    relative_path,
)

LANGUAGE_BY_EXTENSION = {
    ".c": "C",
    ".cc": "C++",
    ".cpp": "C++",
    ".cs": "C#",
    ".css": "CSS",
    ".go": "Go",
    ".html": "HTML",
    ".java": "Java",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".kt": "Kotlin",
    ".php": "PHP",
    ".py": "Python",
    ".rb": "Ruby",
    ".rs": "Rust",
    ".scss": "SCSS",
    ".sh": "Shell",
    ".sql": "SQL",
    ".swift": "Swift",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".vue": "Vue",
}

FRAMEWORK_RULES = {
    "react": ("React", "frontend"),
    "next": ("Next.js", "frontend"),
    "vue": ("Vue", "frontend"),
    "@angular/core": ("Angular", "frontend"),
    "svelte": ("Svelte", "frontend"),
    "vite": ("Vite", "frontend"),
    "express": ("Express", "backend"),
    "fastapi": ("FastAPI", "backend"),
    "flask": ("Flask", "backend"),
    "django": ("Django", "backend"),
    "spring-boot": ("Spring Boot", "backend"),
    "laravel": ("Laravel", "backend"),
    "rails": ("Ruby on Rails", "backend"),
    "gin-gonic": ("Gin", "backend"),
    "actix-web": ("Actix Web", "backend"),
}

DATABASE_RULES = {
    "sqlalchemy": "SQLAlchemy",
    "alembic": "Alembic",
    "psycopg": "PostgreSQL",
    "psycopg2": "PostgreSQL",
    "asyncpg": "PostgreSQL",
    "pymysql": "MySQL",
    "mysqlclient": "MySQL",
    "pymongo": "MongoDB",
    "mongodb": "MongoDB",
    "mongoose": "MongoDB",
    "prisma": "Prisma",
    "drizzle-orm": "Drizzle ORM",
    "sequelize": "Sequelize",
    "typeorm": "TypeORM",
    "sqlite3": "SQLite",
    "better-sqlite3": "SQLite",
    "spring-data-jpa": "JPA",
}

IGNORED_ROOT_FILES = {".env", ".env.local", ".env.production"}
MANIFEST_NAMES = {
    "package.json",
    "requirements.txt",
    "requirements-dev.txt",
    "pyproject.toml",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "composer.json",
    "Cargo.toml",
    "go.mod",
}


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def _find_readme(root: Path) -> tuple[str, str]:
    candidates = [path for path in iter_project_files(root) if path.name.lower() in {"readme.md", "readme.txt", "readme"}]
    if not candidates:
        return "", ""
    path = candidates[0]
    return relative_path(path, root), read_text_file(path)


def _readme_summary(text: str) -> str:
    if not text:
        return "No README detected."
    lines = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith(("#", "```", "![", "---", "- [")):
            continue
        clean = re.sub(r"[*_`>#]", "", line)
        clean = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", clean).strip()
        if clean:
            lines.append(clean)
        if len(" ".join(lines)) >= 520:
            break
    summary = " ".join(lines)
    return (summary[:560].rstrip() + "…") if len(summary) > 560 else (summary or "README detected but no summary text was available.")


def _project_name(root: Path, readme: str) -> str:
    for line in readme.splitlines():
        match = re.match(r"^\s*#\s+(.+?)\s*$", line)
        if match:
            return re.sub(r"[*_`]", "", match.group(1)).strip()

    for path, manifest in load_json_manifests(root):
        if isinstance(manifest.get("name"), str) and manifest["name"].strip():
            return manifest["name"].strip()

    for path in iter_project_files(root):
        if path.name == "pyproject.toml":
            for line in read_text_file(path).splitlines():
                match = re.match(r"\s*name\s*=\s*[\"']([^\"']+)", line)
                if match:
                    return match.group(1)
        if path.name == "Cargo.toml":
            for line in read_text_file(path).splitlines():
                match = re.match(r"\s*name\s*=\s*[\"']([^\"']+)", line)
                if match:
                    return match.group(1)
        if path.name == "go.mod":
            match = re.search(r"^\s*module\s+(\S+)", read_text_file(path), re.MULTILINE)
            if match:
                return match.group(1).rstrip("/").split("/")[-1]
        if path.name == "pom.xml":
            match = re.search(r"<artifactId>\s*([^<]+)\s*</artifactId>", read_text_file(path))
            if match:
                return match.group(1).strip()
    return root.name.removeprefix("codeguard-project-") or "Uploaded project"


def _manifest_text(root: Path) -> str:
    return "\n".join(
        read_text_file(path)
        for path in iter_project_files(root)
        if path.name in MANIFEST_NAMES or path.name in {"vite.config.js", "vite.config.ts", "docker-compose.yml", "docker-compose.yaml"}
    )


def _languages(root: Path) -> list[str]:
    counts: defaultdict[str, int] = defaultdict(int)
    for path in iter_project_files(root):
        language = LANGUAGE_BY_EXTENSION.get(path.suffix.lower())
        if language:
            counts[language] += 1
    return [name for name, _ in sorted(counts.items(), key=lambda item: (-item[1], item[0]))]


def _frameworks_and_libraries(root: Path) -> tuple[list[str], list[str], str, str]:
    names = {name.lower() for name in dependency_names(root)}
    text = _manifest_text(root).lower()
    frameworks: list[str] = []
    frontend: list[str] = []
    backend: list[str] = []
    for package_name, (label, area) in FRAMEWORK_RULES.items():
        if package_name.lower() in names or package_name.lower() in text:
            frameworks.append(label)
            (frontend if area == "frontend" else backend).append(label)

    libraries = []
    framework_keys = set(FRAMEWORK_RULES)
    for name in sorted(names):
        if name not in framework_keys and name not in {"python", "node", "nodejs"}:
            libraries.append(name)

    return _unique(frameworks), _unique(libraries), ", ".join(frontend) or "Not detected", ", ".join(backend) or "Not detected"


def _database(root: Path) -> str:
    names = {name.lower() for name in dependency_names(root)}
    text = _manifest_text(root).lower()
    matches = [label for package_name, label in DATABASE_RULES.items() if package_name.lower() in names or package_name.lower() in text]
    if re.search(r"\b(postgres|postgresql)\b", text):
        matches.append("PostgreSQL")
    if re.search(r"\bmysql\b", text):
        matches.append("MySQL")
    if re.search(r"\bmongodb\b", text):
        matches.append("MongoDB")
    return ", ".join(_unique(matches)) or "Not detected"


def _project_type(root: Path, frameworks: list[str], languages: list[str], database: str) -> str:
    lower_frameworks = {framework.lower() for framework in frameworks}
    if any(framework in lower_frameworks for framework in {"react", "next.js", "vue", "angular", "svelte"}):
        return "Web Application"
    if any(framework in lower_frameworks for framework in {"fastapi", "flask", "django", "express", "spring boot", "laravel", "ruby on rails"}):
        return "Backend Service"
    if "java" in {language.lower() for language in languages} and "pom.xml" in {path.name for path in iter_project_files(root)}:
        return "Java Application"
    if database != "Not detected":
        return "Data Application"
    return "Software Project"


def _folder_structure(root: Path) -> dict[str, Any]:
    tree: dict[str, Any] = {}
    for path in iter_project_files(root):
        relative = path.relative_to(root)
        current = tree
        for part in relative.parts[:-1]:
            current = current.setdefault(part, {})
        current.setdefault("_files", []).append(relative.parts[-1])
    return tree


def _tests(root: Path) -> list[str]:
    test_files = []
    for path in iter_project_files(root):
        lower_parts = {part.lower() for part in path.parts}
        name = path.name.lower()
        if (
            "test" in lower_parts
            or "tests" in lower_parts
            or name.startswith("test_")
            or name.endswith("_test.py")
            or name.endswith(".test.js")
            or name.endswith(".test.ts")
            or name.endswith(".spec.js")
            or name.endswith(".spec.ts")
            or name.endswith(".spec.tsx")
        ):
            test_files.append(relative_path(path, root))
    return test_files[:100]


def _entry_points(root: Path, manifests: list[tuple[str, dict[str, Any]]]) -> list[str]:
    candidates = {
        "main.py",
        "app.py",
        "manage.py",
        "main.js",
        "main.ts",
        "main.tsx",
        "index.js",
        "index.ts",
        "index.tsx",
        "server.js",
        "server.ts",
        "pom.xml",
        "go.mod",
        "Cargo.toml",
    }
    entries = [relative_path(path, root) for path in iter_project_files(root) if path.name in candidates]
    for path, manifest in manifests:
        for key in ("main", "module", "bin"):
            value = manifest.get(key)
            if isinstance(value, str):
                entries.append(value)
            elif isinstance(value, dict):
                entries.extend(str(item) for item in value.values() if isinstance(item, str))
        scripts = manifest.get("scripts", {})
        if isinstance(scripts, dict):
            for key in ("start", "dev"):
                if key in scripts:
                    entries.append(f"{path} ({key} script)")
    return _unique(entries)[:40]


def _apis(root: Path, frameworks: list[str]) -> list[str]:
    matches: list[str] = []
    route_patterns = [
        (r"@\w+\.(?:get|post|put|patch|delete)\s*\(", "HTTP routes"),
        (r"\b(?:app|router)\.(?:get|post|put|patch|delete)\s*\(", "HTTP routes"),
        (r"\b(?:fetch|axios\.(?:get|post|put|patch|delete))\s*\(", "HTTP client calls"),
    ]
    evidence_files: set[str] = set()
    for path in iter_project_files(root):
        text = read_text_file(path)
        if not text:
            continue
        for pattern, label in route_patterns:
            if re.search(pattern, text):
                matches.append(label)
                evidence_files.add(relative_path(path, root))
    if "FastAPI" in frameworks or "Express" in frameworks or "Flask" in frameworks or "Django" in frameworks:
        matches.append("Web API framework")
    if evidence_files and matches:
        matches.append(f"Route evidence in {sorted(evidence_files)[0]}")
    return _unique(matches)


def _features(root: Path, frameworks: list[str], database: str, apis: list[str], tests: list[str], readme: str) -> list[str]:
    features: list[str] = []
    file_names = {path.name.lower() for path in iter_project_files(root)}
    all_text = "\n".join(read_text_file(path) for path in iter_project_files(root)[:300]).lower()
    if apis:
        features.append("HTTP/API communication")
    if database != "Not detected":
        features.append("Database integration")
    if any(framework in frameworks for framework in {"React", "Next.js", "Vue", "Angular", "Svelte"}):
        features.append("Frontend interface")
    if tests:
        features.append("Automated tests")
    if "dockerfile" in file_names or "docker-compose.yml" in file_names or "docker-compose.yaml" in file_names:
        features.append("Containerized development")
    if "requirements.txt" in file_names or "package.json" in file_names or "pyproject.toml" in file_names:
        features.append("Dependency-managed project")
    if readme:
        features.append("Project documentation")
    for label, pattern in (
        ("Authentication flow", r"\b(?:login|logout|sign[- ]?up|authentication|authorize)\b"),
        ("File handling", r"\b(?:upload|download|multipart|file upload)\b"),
    ):
        if re.search(pattern, all_text):
            features.append(label)
    return _unique(features)


def _important_files(root: Path, readme_path: str, entries: list[str], tests: list[str]) -> list[str]:
    files = []
    for path in iter_project_files(root):
        rel = relative_path(path, root)
        if path.name in MANIFEST_NAMES or path.name.lower() in {"dockerfile", "docker-compose.yml", "docker-compose.yaml"}:
            files.append(rel)
        elif path.name in IGNORED_ROOT_FILES:
            continue
    files.extend([readme_path, *entries[:8], *tests[:4]])
    return _unique(files)[:60]


def profile_project(root: Path, project_id: str) -> ProjectProfile:
    readme_path, readme = _find_readme(root)
    manifests = load_json_manifests(root)
    languages = _languages(root)
    frameworks, libraries, frontend, backend = _frameworks_and_libraries(root)
    database = _database(root)
    tests = _tests(root)
    entries = _entry_points(root, manifests)
    apis = _apis(root, frameworks)
    return ProjectProfile(
        project_id=project_id,
        project_name=_project_name(root, readme),
        project_type=_project_type(root, frameworks, languages, database),
        languages=languages,
        frameworks=frameworks,
        libraries=libraries[:80],
        frontend=frontend,
        backend=backend,
        database=database,
        apis=apis,
        modules=_unique(
            [path.relative_to(root).parts[0] for path in iter_project_files(root) if len(path.relative_to(root).parts) > 1]
        )[:40],
        features=_features(root, frameworks, database, apis, tests, readme),
        entry_points=entries,
        readme_summary=_readme_summary(readme),
        folder_structure=_folder_structure(root),
        tests=tests,
        important_files=_important_files(root, readme_path, entries, tests),
    )
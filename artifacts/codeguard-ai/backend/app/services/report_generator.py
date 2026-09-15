"""Fast, local report generation grounded in the analyzed project profile."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

MAX_SAMPLE_CHARS = 6000
NOT_DETECTED = "Not detected"
NOT_PROVIDED = "Not provided"

DEFAULT_SECTIONS: list[tuple[str, str]] = [
    ("abstract", "Abstract"),
    ("introduction", "Introduction"),
    ("objectives", "Objectives"),
    ("system-requirements", "System Requirements"),
    ("technology-stack", "Technology Stack"),
    ("system-architecture", "System Architecture"),
    ("modules", "Modules Description"),
    ("features", "Features and Functionality"),
    ("implementation", "Implementation Details"),
    ("testing", "Testing"),
    ("conclusion", "Conclusion"),
]


class ReportGenerationError(RuntimeError):
    """Raised when local report generation cannot produce a section."""

    status_code = 500


@dataclass
class GenerationContext:
    facts: str
    instructions: str
    sample_style: str


def slugify(title: str, index: int) -> str:
    slug = "".join(char.lower() if char.isalnum() else "-" for char in title).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug or f"section-{index + 1}"


def _value(value: Any) -> str:
    text = str(value or "").strip()
    return text or NOT_DETECTED


def _values(values: Any) -> list[str]:
    result = [str(item).strip() for item in (values or []) if str(item).strip()]
    return result or [NOT_DETECTED]


def build_facts(profile) -> str:
    facts = {
        "project_name": _value(getattr(profile, "project_name", "")),
        "project_type": _value(getattr(profile, "project_type", "")),
        "languages": _values(getattr(profile, "languages", [])),
        "frameworks": _values(getattr(profile, "frameworks", [])),
        "libraries": _values(getattr(profile, "libraries", [])),
        "frontend": _value(getattr(profile, "frontend", "")),
        "backend": _value(getattr(profile, "backend", "")),
        "database": _value(getattr(profile, "database", "")),
        "apis": _values(getattr(profile, "apis", [])),
        "modules": _values(getattr(profile, "modules", [])),
        "features": _values(getattr(profile, "features", [])),
        "entry_points": _values(getattr(profile, "entry_points", [])),
        "tests": _values(getattr(profile, "tests", [])),
        "important_files": _values(getattr(profile, "important_files", [])),
        "readme_summary": _value(getattr(profile, "readme_summary", "")),
        "folder_structure": getattr(profile, "folder_structure", {}) or {},
    }
    return json.dumps(facts, indent=2, default=str)


def build_sample_style(sample_text: str) -> str:
    return (sample_text or "").strip()[:MAX_SAMPLE_CHARS]


def build_context(profile, instructions: str = "", sample_text: str = "") -> GenerationContext:
    return GenerationContext(
        facts=build_facts(profile),
        instructions=(instructions or "").strip(),
        sample_style=build_sample_style(sample_text),
    )


def _facts(context: GenerationContext) -> dict[str, Any]:
    try:
        value = json.loads(context.facts)
        return value if isinstance(value, dict) else {}
    except json.JSONDecodeError:
        return {}


def _join(values: Any) -> str:
    return ", ".join(_values(values))


def _sample_headings(sample: str) -> list[str]:
    headings: list[str] = []
    for raw_line in sample.splitlines():
        line = re.sub(r"^\s*(?:#+|\d+(?:\.\d+)*[.)])\s*", "", raw_line).strip()
        if not line or len(line) > 90:
            continue
        if raw_line.lstrip().startswith("#") or re.match(r"^\d+(?:\.\d+)*[.)]\s+", raw_line):
            headings.append(line)
    unique = list(dict.fromkeys(headings))
    return unique[:14] if len(unique) >= 3 else []


def plan_sections(context: GenerationContext) -> list[tuple[str, str]]:
    titles = _sample_headings(context.sample_style)
    if not titles:
        return list(DEFAULT_SECTIONS)
    return [(slugify(title, index), title) for index, title in enumerate(titles)]


def _section_body(title: str, facts: dict[str, Any]) -> str:
    name = _value(facts.get("project_name"))
    project_type = _value(facts.get("project_type"))
    languages = _join(facts.get("languages"))
    frameworks = _join(facts.get("frameworks"))
    libraries = _join(facts.get("libraries"))
    frontend = _value(facts.get("frontend"))
    backend = _value(facts.get("backend"))
    database = _value(facts.get("database"))
    modules = _join(facts.get("modules"))
    features = _join(facts.get("features"))
    apis = _join(facts.get("apis"))
    tests = _join(facts.get("tests"))
    entries = _join(facts.get("entry_points"))
    summary = _value(facts.get("readme_summary"))
    key = title.lower()

    if "abstract" in key:
        return f"{name} is classified as {project_type}. The analyzed project uses {languages}; detected frameworks are {frameworks}. A concise project summary from the available documentation is: {summary}."
    if "introduction" in key:
        return f"This section introduces {name}, identified as a {project_type}. The available README evidence describes the project as follows: {summary}. Author, institution, dates, and broader context are {NOT_PROVIDED}."
    if "objective" in key:
        return f"The available evidence supports the objective of describing and implementing the analyzed {project_type}. Detected features are {features}. Specific user-provided objectives and measurable targets are {NOT_PROVIDED}."
    if "requirement" in key:
        return f"The detected implementation areas are frontend: {frontend}; backend: {backend}; and database: {database}. Entry points identified in the project are {entries}. Detailed functional, hardware, and deployment requirements are {NOT_DETECTED}."
    if "technology" in key or "stack" in key:
        return f"The technology evidence identifies languages {languages}, frameworks {frameworks}, and libraries {libraries}. The detected database technology is {database}. Technologies not present in the analyzed files are {NOT_DETECTED}."
    if "architect" in key:
        return f"The analyzed project contains frontend evidence {frontend}, backend evidence {backend}, and API evidence {apis}. Its detected top-level modules are {modules}. A runtime deployment topology and external infrastructure details are {NOT_DETECTED}."
    if "module" in key:
        return f"The project modules detected from its file structure are {modules}. Important entry points include {entries}. Module responsibilities beyond the available file and README evidence are {NOT_DETECTED}."
    if "feature" in key or "function" in key:
        return f"The detected features are {features}. API evidence is {apis}. This description is limited to behavior indicated by analyzed files; undocumented features are {NOT_DETECTED}."
    if "implement" in key:
        return f"Implementation evidence is present in the entry points {entries}, using languages {languages} and frameworks {frameworks}. The analyzed project also references libraries {libraries}. Undocumented algorithms, metrics, and deployment details are {NOT_DETECTED}."
    if "test" in key or "quality" in key:
        return f"The project contains the following detected test evidence: {tests}. Test results, coverage values, performance measurements, and quality claims are {NOT_PROVIDED}."
    if "conclu" in key or "result" in key:
        return f"The analysis confirms a {project_type} named {name}, with detected features {features} and technologies {frameworks}. Measured results, limitations, and future work are {NOT_PROVIDED}."
    return f"The section titled {title} is grounded in the analyzed project {name}. Relevant detected modules are {modules}, technologies are {frameworks}, and features are {features}. Additional section-specific evidence is {NOT_DETECTED}."


def generate_section(section_title: str, context: GenerationContext) -> str:
    return _section_body(section_title, _facts(context))


def regenerate_section(section_title: str, context: GenerationContext, previous_content: str = "") -> str:
    return generate_section(section_title, context)

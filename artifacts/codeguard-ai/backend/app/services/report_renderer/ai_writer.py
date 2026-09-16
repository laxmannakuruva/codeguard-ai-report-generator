"""AI report writer — supports Ollama (local) and Groq (cloud)."""

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

# Load .env from the repo root so env vars are available in dev and prod.
try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).resolve().parents[6] / ".env"
    if _env_path.exists():
        load_dotenv(_env_path)
except Exception:
    pass

AI_PROVIDER = os.getenv("AI_PROVIDER", "ollama").strip().lower()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

TIMEOUT_SECONDS = 600


SECTION_SPECS = [
    {
        "title": "Abstract",
        "focus_keys": ["project_name", "project_type", "readme_summary", "features"],
        "instruction": (
            "Write a formal academic abstract of 220-280 words. "
            "Cover: what the project is, what problem it solves, what technologies it uses, "
            "what it produces, and its main outcome. "
            "Do not repeat the same sentence twice."
        ),
    },
    {
        "title": "Introduction",
        "focus_keys": ["project_name", "project_type", "readme_summary"],
        "instruction": (
            "Write 350-450 words introducing the project. "
            "Cover the domain, why automated project analysis matters, and the project's goal. "
            "Open with a general statement about the problem space, then narrow to this project."
        ),
    },
    {
        "title": "Background and Problem Statement",
        "focus_keys": ["project_name", "readme_summary", "features"],
        "instruction": (
            "Write 350-450 words. Explain the specific problem this project addresses. "
            "Describe what the current manual or existing approach looks like, its limitations, "
            "and why this project is needed. End with a clear problem statement."
        ),
    },
    {
        "title": "Methodology",
        "focus_keys": ["languages", "frameworks", "libraries", "backend", "frontend", "database"],
        "instruction": (
            "Write 400-500 words describing the development methodology. "
            "Focus ONLY on technologies: languages, frameworks, libraries, backend, frontend, database. "
            "Explain how they were chosen and how they work together. Do not repeat the project's purpose."
        ),
    },
    {
        "title": "System Architecture and Implementation",
        "focus_keys": ["modules", "entry_points", "apis", "folder_structure", "important_files"],
        "instruction": (
            "Write 400-500 words describing the system architecture and implementation. "
            "Focus ONLY on structure: modules, entry points, APIs, folder organization, key files. "
            "Describe how the components fit together technically."
        ),
    },
    {
        "title": "Features and Functionality",
        "focus_keys": ["features", "apis", "modules"],
        "instruction": (
            "Write 350-450 words describing the specific features the project provides. "
            "Focus ONLY on capabilities: what a user can do, what each feature does, how APIs support them. "
            "Do not repeat architecture details."
        ),
    },
    {
        "title": "Results and Discussion",
        "focus_keys": ["project_name", "features", "readme_summary"],
        "instruction": (
            "Write 300-400 words discussing the results. "
            "Describe what the finished project produces as output, its working state, "
            "and any observable characteristics. Do not invent metrics or performance numbers."
        ),
    },
    {
        "title": "Outcomes and Learning",
        "focus_keys": ["languages", "frameworks", "libraries"],
        "instruction": (
            "Write 300-400 words describing the skills and knowledge gained. "
            "Focus ONLY on technologies and engineering practices: what was learned from working with "
            "these specific languages, frameworks, and tools."
        ),
    },
    {
        "title": "Conclusions and Recommendations",
        "focus_keys": ["project_name", "features", "languages", "frameworks"],
        "instruction": (
            "Write 400-500 words. First summarize the project in 2 paragraphs, then give "
            "5-7 concrete recommendations for future enhancement. "
            "Number the recommendations and make each one specific to this technology stack."
        ),
    },
    {
        "title": "Acknowledgement",
        "focus_keys": ["project_name"],
        "instruction": (
            "Write 200-250 words of formal academic acknowledgement. "
            "Thank the academic institution, project guide, and any collaborators generically. "
            "Do not invent specific names, only reference generic roles. "
            "Use professional, warm academic tone."
        ),
    },
    {
        "title": "References",
        "focus_keys": ["languages", "frameworks", "libraries", "backend", "frontend", "database"],
        "instruction": (
            "Write a formal references list with 10-14 entries. "
            "Use ONLY official documentation sources for the technologies listed in the facts "
            "(e.g., Python.org, FastAPI docs, React docs). "
            "Format each entry in a consistent academic style. Do not invent papers or authors. "
            "One reference per line, numbered."
        ),
    },
]


def _facts_subset(facts, keys):
    lines = []
    for key in keys:
        value = facts.get(key)
        if not value:
            continue
        if isinstance(value, (list, tuple)):
            value = ", ".join(str(v) for v in value if v)
        value = str(value).strip()
        if value and value.lower() not in ("not detected", "not provided", "none"):
            lines.append(f"- {key.replace('_', ' ').title()}: {value}")
    return "\n".join(lines) if lines else "- (limited facts)"


def _build_prompt(title, instruction, subset):
    return (
        "You are writing a section of a formal academic internship report.\n\n"
        "STRICT RULES:\n"
        "1. Use ONLY the facts listed below.\n"
        "2. Do NOT invent names, dates, organisations, metrics, or statistics.\n"
        "3. Do NOT repeat the same sentence that appears in other sections.\n"
        "4. Write in flowing academic prose. No bullet points, no markdown, no headings.\n"
        "5. Do NOT start with 'CodeGuard AI is a full-stack web application...'.\n"
        "6. Vary your opening sentence for each section.\n"
        "7. Aim for depth and specificity, not generic filler.\n\n"
        f"FACTS FOR THIS SECTION:\n{subset}\n\n"
        f"SECTION TITLE: {title}\n"
        f"INSTRUCTIONS: {instruction}\n\n"
        "Return ONLY the paragraph body. No heading. No commentary."
    )


def _call_ollama(prompt):
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.55, "num_predict": 1000, "num_ctx": 4096},
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/generate",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
        body = resp.read().decode("utf-8")
    return (json.loads(body).get("response") or "").strip()


def _call_groq(prompt):
    """Call Groq via the official SDK with a fallback chain.

    Treats responses under 200 characters as failures (likely refusals),
    and tries the next model. Each model gets 2 attempts.
    """
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is not set but AI_PROVIDER=groq")

    from groq import Groq

    client = Groq(api_key=GROQ_API_KEY, timeout=TIMEOUT_SECONDS)

    models_to_try = [
        GROQ_MODEL,
        "openai/gpt-oss-120b",
        "qwen/qwen3.8-27b",
        "groq/compound-mini",
        "groq/compound",
    ]

    system_prompt = (
        "You are a professional academic writer. "
        "You write formal, detailed paragraphs for internship reports. "
        "Always produce the full requested word count. "
        "Never refuse a writing task. "
        "Never output apologies or disclaimers."
    )

    for model_name in models_to_try:
        for attempt in range(2):
            try:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.6 + (0.1 * attempt),
                    max_tokens=1500,
                )
                if response.choices:
                    content = (response.choices[0].message.content or "").strip()
                    if len(content) >= 200:
                        return content
            except Exception:
                continue

    return ""


def _call_ai(prompt):
    if AI_PROVIDER == "groq":
        return _call_groq(prompt)
    return _call_ollama(prompt)


def generate_sections(facts, progress=None):
    out = []
    for i, spec in enumerate(SECTION_SPECS, start=1):
        title = spec["title"]
        if progress:
            progress(f"[{i}/{len(SECTION_SPECS)}] {title}...")
        subset = _facts_subset(facts, spec["focus_keys"])
        prompt = _build_prompt(title, spec["instruction"], subset)
        try:
            content = _call_ai(prompt)
        except Exception as exc:
            content = f"[AI generation failed: {exc}]"
        if not content:
            content = "[AI returned empty content]"
        out.append({"title": title, "content": content})
        if progress:
            progress(f"    -> {len(content)} chars")
    return out
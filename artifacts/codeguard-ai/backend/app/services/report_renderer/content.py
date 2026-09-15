"""Normalize profile + sections into template context."""

import json
import re
from dataclasses import dataclass, field
from html import escape

CONFLICT_RE = re.compile(
    r"<<<<<<<.*?(?:\n|$)|=======.*?(?:\n|$)|>>>>>>>.*?(?:\n|$)", re.S
)
DETECTED = "Not detected"
PROVIDED = "Not provided"
FIELDS = (
    "project_name", "project_type", "languages", "frameworks", "libraries",
    "frontend", "backend", "database", "apis", "modules", "features",
    "entry_points", "tests", "important_files", "readme_summary", "folder_structure",
)


def _clean(v):
    if v is None:
        return ""
    return re.sub(r"[ \t]+", " ", CONFLICT_RE.sub("", str(v))).strip()


def _read_profile(p):
    if p is None:
        return {}
    if all(hasattr(p, f) for f in FIELDS):
        return {f: getattr(p, f) for f in FIELDS}
    fs = getattr(p, "facts", None)
    if isinstance(fs, str):
        try:
            d = json.loads(fs)
            if isinstance(d, dict):
                return d
        except Exception:
            pass
    if isinstance(p, dict):
        return dict(p)
    out = {f: getattr(p, f) for f in FIELDS if hasattr(p, f)}
    if out:
        return out
    for m in ("model_dump", "dict"):
        fn = getattr(p, m, None)
        if callable(fn):
            try:
                d = fn()
                if isinstance(d, dict):
                    return d
            except Exception:
                pass
    return {}


def _as_list(v):
    if v is None:
        return []
    if isinstance(v, str):
        s = v.strip()
        if s.startswith("[") and s.endswith("]"):
            try:
                p = json.loads(s)
                if isinstance(p, list):
                    return [_clean(x) for x in p if _clean(x)]
            except Exception:
                pass
        return [_clean(x) for x in re.split(r"[\n,]", s) if _clean(x)]
    if isinstance(v, (list, tuple, set)):
        return [_clean(x) for x in v if _clean(x)]
    return [_clean(v)]


def _join(items, sep=", "):
    items = [x for x in items if x]
    return escape(sep.join(items)) if items else DETECTED


@dataclass
class Section:
    title: str
    paragraphs: list = field(default_factory=list)
    heading: str = None


def _paras(text):
    text = CONFLICT_RE.sub("", text or "")
    if not text.strip():
        return []
    out = []
    for b in re.split(r"\n\s*\n", text):
        b = re.sub(r"^#{1,6}\s*", "", b, flags=re.MULTILINE)
        c = " ".join(l.strip() for l in b.splitlines() if l.strip())
        if c:
            out.append(c)
    return out


def _section(obj, i):
    if obj is None:
        return Section(f"Section {i}")
    if isinstance(obj, dict):
        title = obj.get("title") or obj.get("name") or f"Section {i}"
        content = obj.get("content") or obj.get("body") or ""
    else:
        title = getattr(obj, "title", None) or getattr(obj, "name", None) or f"Section {i}"
        content = getattr(obj, "content", None) or getattr(obj, "body", None) or ""
    title = _clean(title) or f"Section {i}"
    return Section(title, _paras(content if isinstance(content, str) else str(content)))


def build_context(profile, sections):
    f = _read_profile(profile)
    pn = _clean(f.get("project_name")) or DETECTED
    pt = _clean(f.get("project_type")) or DETECTED

    chapters = []
    for i, raw in enumerate(sections or [], 1):
        s = _section(raw, i)
        if s.title.strip().lower() == "abstract":
            continue
        chapters.append(s)
    for i, s in enumerate(chapters, 1):
        s.heading = f"{i}. {s.title}"

    langs = _as_list(f.get("languages"))
    fw = _as_list(f.get("frameworks"))
    libs = _as_list(f.get("libraries"))
    fe = _as_list(f.get("frontend"))
    be = _as_list(f.get("backend"))
    db = _as_list(f.get("database"))
    apis = _as_list(f.get("apis"))
    mods = _as_list(f.get("modules"))
    feats = _as_list(f.get("features"))
    eps = _as_list(f.get("entry_points"))
    tst = _as_list(f.get("tests"))
    imp = _as_list(f.get("important_files"))
    fold = _as_list(f.get("folder_structure"))

    return {
        "project_name": escape(pn),
        "project_type": escape(pt),
        "languages": langs,
        "frameworks": fw,
        "libraries": libs,
        "frontend": fe,
        "backend": be,
        "database": db,
        "apis": apis,
        "modules": mods,
        "features": feats,
        "entry_points": eps,
        "tests": tst,
        "important_files": imp,
        "folder_structure": fold,
        "languages_text": _join(langs),
        "frameworks_text": _join(fw),
        "libraries_text": _join(libs),
        "frontend_text": _join(fe),
        "backend_text": _join(be),
        "database_text": _join(db),
        "apis_text": _join(apis),
        "modules_text": _join(mods),
        "features_text": _join(feats),
        "entry_points_text": _join(eps),
        "tests_text": _join(tst),
        "readme_summary": escape(_clean(f.get("readme_summary")) or PROVIDED),
        "chapters": chapters,
    }
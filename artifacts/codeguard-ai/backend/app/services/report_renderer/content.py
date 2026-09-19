"""Normalize profile + sections into template context."""

import ast
import html
import json
import re
from dataclasses import dataclass, field
from html import escape

CONFLICT_RE = re.compile(
    r"<<<<<<<.*?(?:\n|$)|=======.*?(?:\n|$)|>>>>>>>.*?(?:\n|$)", re.S
)
NUMBERED_LINE_RE = re.compile(r"^\s*(\d{1,3})[.)]\s+(.+)$")
BULLET_LINE_RE = re.compile(r"^\s*[-*•]\s+(.+)$")
# Finds N. followed by uppercase anywhere — including after URLs like "/2. Mozilla"
INLINE_NUMBERED_RE = re.compile(r"(\d{1,3})[.)]\s+(?=[A-Z])")

# Markdown patterns
MD_ESCAPED_RE = re.compile(r"\\([*_`~#])")
MD_BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")
MD_BOLD_ALT_RE = re.compile(r"__([^_]+)__")
MD_ITALIC_RE = re.compile(r"(?<!\*)\*([^*\n]+)\*(?!\*)")
MD_ITALIC_ALT_RE = re.compile(r"(?<!_)_([^_\n]+)_(?!_)")
MD_HEADING_RE = re.compile(r"^#{1,6}\s+", re.MULTILINE)
MD_HEADING_LINE_RE = re.compile(r"^\s*#{1,6}\s+(.+)$")
MD_TABLE_ROW_RE = re.compile(r"^\s*\|(.+)\|\s*$")
MD_TABLE_SEP_RE = re.compile(r"^\s*[\|\s\-:]*-{3,}[\|\s\-:]*$")
MD_FIGURE_RE = re.compile(r"^\s*\[FIGURE:\s*(.+?)\]\s*$", re.IGNORECASE)
EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001F9FF"
    "\U00002600-\U000027BF"
    "\U0001F000-\U0001F0FF"
    "\U0001F900-\U0001F9FF"
    "\u2600-\u27BF"
    "\u2190-\u21FF"
    "\u2B00-\u2BFF"
    "\uFE00-\uFE0F"
    "\u200D"
    "]+",
    flags=re.UNICODE,
)
MD_CODE_RE = re.compile(r"`([^`]+)`")

DETECTED = "Not detected"
PROVIDED = "Not provided"
FIELDS = (
    "project_name", "project_type", "languages", "frameworks", "libraries",
    "frontend", "backend", "database", "apis", "modules", "features",
    "entry_points", "tests", "important_files", "readme_summary", "folder_structure",
)


def _strip_markdown(s):
    s = MD_ESCAPED_RE.sub(r"\1", s)
    s = MD_BOLD_RE.sub(r"\1", s)
    s = MD_BOLD_ALT_RE.sub(r"\1", s)
    s = MD_ITALIC_RE.sub(r"\1", s)
    s = MD_ITALIC_ALT_RE.sub(r"\1", s)
    s = MD_HEADING_RE.sub("", s)
    s = MD_CODE_RE.sub(r"\1", s)
    return s


def _clean(v):
    if v is None:
        return ""
    s = CONFLICT_RE.sub("", str(v))
    s = html.unescape(html.unescape(html.unescape(s)))
    s = _strip_markdown(s)
    s = EMOJI_RE.sub("", s)
    return re.sub(r"[ \t]+", " ", s).strip()


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


def _flatten_folder_structure(fs):
    """Convert nested folder dict OR list into clean list of path strings."""
    if fs is None:
        return []

    if isinstance(fs, str):
        s = fs.strip()
        if s.startswith("[") or s.startswith("{"):
            try:
                fs = ast.literal_eval(s)
            except Exception:
                try:
                    fs = json.loads(s)
                except Exception:
                    return [x.strip() for x in re.split(r"[\n,]", s) if x.strip()]
        else:
            return [x.strip() for x in re.split(r"[\n,]", s) if x.strip()]

    out = []

    def walk(node, prefix):
        if isinstance(node, dict):
            files = node.get("_files") or node.get("files") or []
            if isinstance(files, list):
                for f in files:
                    path = f"{prefix}/{f}" if prefix else str(f)
                    out.append(path)
            for k, v in node.items():
                if k in ("_files", "files"):
                    continue
                child_prefix = f"{prefix}/{k}" if prefix else str(k)
                walk(v, child_prefix)
        elif isinstance(node, list):
            for f in node:
                path = f"{prefix}/{f}" if prefix else str(f)
                out.append(path)

    walk(fs, "")
    return sorted(set(out))


def _shorten_paths(paths):
    """Drop the common top-level root segment from every path."""
    if not paths:
        return paths
    roots = {p.split("/")[0] for p in paths if "/" in p}
    if len(roots) == 1:
        root = roots.pop()
        return ["/".join(p.split("/")[1:]) if p.startswith(root + "/") else p for p in paths]
    return paths


def _render_tree(paths):
    """Turn a flat list of slash-paths into an ASCII tree string."""
    if not paths:
        return []
    tree = {}
    for p in paths:
        cur = tree
        for part in p.split("/"):
            cur = cur.setdefault(part, {})
    lines = []

    def walk(node, prefix=""):
        items = sorted(node.items())
        for i, (name, sub) in enumerate(items):
            last = (i == len(items) - 1)
            conn = "└── " if last else "├── "
            lines.append(prefix + conn + name)
            if sub:
                walk(sub, prefix + ("    " if last else "│   "))

    walk(tree)
    return lines


def _join(items, sep=", "):
    items = [x for x in items if x]
    return escape(sep.join(items)) if items else DETECTED


@dataclass
class Block:
    type: str
    text: str = ""
    items: list = field(default_factory=list)
    image_uri: str = ""


@dataclass
class Section:
    title: str
    paragraphs: list = field(default_factory=list)
    blocks: list = field(default_factory=list)
    heading: str = None


def _pre_split_inline_numbers(text):
    """Split '1. X 2. Y 3. Z' into separate lines."""
    out = []
    for raw_line in text.split("\n"):
        matches = list(INLINE_NUMBERED_RE.finditer(raw_line))
        if len(matches) >= 2:
            # Ensure numbers are sequential (1, 2, 3...) not random years etc.
            nums = [int(m.group(1)) for m in matches]
            sequential = nums == list(range(nums[0], nums[0] + len(nums)))
            if sequential and len(nums) >= 3:
                pieces = []
                for i, m in enumerate(matches):
                    start = m.start()
                    end = matches[i + 1].start() if i + 1 < len(matches) else len(raw_line)
                    pieces.append(raw_line[start:end].strip())
                if matches[0].start() > 0:
                    head = raw_line[: matches[0].start()].strip()
                    if head:
                        out.append(head)
                out.extend(pieces)
                continue
        out.append(raw_line)
    return "\n".join(out)


def _parse_blocks(text):
    if not text or not text.strip():
        return []

    text = CONFLICT_RE.sub("", text)
    text = _pre_split_inline_numbers(text)

    lines = text.split("\n")
    blocks = []
    buffer = []
    ol_items = []
    ul_items = []
    table_rows = []
    last_heading = [None]

    def flush_table():
        nonlocal table_rows
        if table_rows:
            rows = [[_clean(c) for c in row] for row in table_rows]
            rows = [r for r in rows if any(r)]
            if rows:
                blocks.append(Block(type="table", items=rows))
            table_rows = []

    def flush_paragraph():
        if buffer:
            joined = " ".join(l.strip() for l in buffer if l.strip())
            joined = _clean(joined)
            h = last_heading[0]
            if h and joined and joined.startswith(h):
                joined = joined[len(h):].lstrip(":.").strip()
            if joined:
                blocks.append(Block(type="p", text=joined))
            buffer.clear()
            last_heading[0] = None

    def flush_list():
        nonlocal ol_items, ul_items
        if ol_items:
            blocks.append(Block(type="ol", items=[_clean(x) for x in ol_items]))
            ol_items = []
        if ul_items:
            blocks.append(Block(type="ul", items=[_clean(x) for x in ul_items]))
            ul_items = []

    for raw_line in lines:
        line = raw_line.rstrip()
        if not line.strip():
            flush_paragraph()
            flush_list()
            continue

        m_heading = MD_HEADING_LINE_RE.match(line)
        m_figure = MD_FIGURE_RE.match(line)
        m_table_sep = MD_TABLE_SEP_RE.match(line)
        m_table_row = MD_TABLE_ROW_RE.match(line)

        if m_table_sep:
            continue

        if m_table_row:
            flush_paragraph()
            flush_list()
            cells = [c.strip() for c in m_table_row.group(1).split("|")]
            table_rows.append(cells)
            continue

        if m_heading:
            flush_table()
            flush_paragraph()
            flush_list()
            raw_h = m_heading.group(1).strip()
            inline = ""
            if ": " in raw_h:
                head, rest = raw_h.split(": ", 1)
                if rest[:1].isupper() and len(head) < 90:
                    raw_h, inline = head, rest
            htext = _clean(raw_h)
            if htext:
                blocks.append(Block(type="h2", text=htext))
                last_heading[0] = htext
            if inline:
                buffer.append(inline)
            continue

        if m_figure:
            continue

        flush_table()

        m_num = NUMBERED_LINE_RE.match(line)
        m_bul = BULLET_LINE_RE.match(line)

        if m_num:
            flush_paragraph()
            if ul_items:
                flush_list()
            ol_items.append(m_num.group(2))
        elif m_bul:
            flush_paragraph()
            if ol_items:
                flush_list()
            ul_items.append(m_bul.group(1))
        else:
            if ol_items or ul_items:
                flush_list()
            buffer.append(line)

    flush_table()
    flush_paragraph()
    flush_list()
    return blocks


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
    if not isinstance(content, str):
        content = str(content)
    blocks = _parse_blocks(content)
    paragraphs = [b.text for b in blocks if b.type == "p"]
    return Section(title=title, paragraphs=paragraphs, blocks=blocks)


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
    fold = _flatten_folder_structure(f.get("folder_structure"))

    eps_short = _shorten_paths(eps)
    imp_short = _shorten_paths(imp)
    fold_short = _shorten_paths(fold)

    return {
        "folder_tree": _render_tree(fold_short),
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
        "entry_points": eps_short,
        "tests": tst,
        "important_files": imp_short,
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
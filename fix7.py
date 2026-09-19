from pathlib import Path

B = Path(r"D:\codeguard-ai-stage3\artifacts\codeguard-ai\backend")
RR = B / "app" / "services" / "report_renderer"

# 1. content.py — add image_uri field
p = RR / "content.py"
s = p.read_text(encoding="utf-8")
old = '''@dataclass
class Block:
    type: str
    text: str = ""
    items: list = field(default_factory=list)'''
new = '''@dataclass
class Block:
    type: str
    text: str = ""
    items: list = field(default_factory=list)
    image_uri: str = ""'''
if old in s and "image_uri" not in s.split("class Block")[1][:200]:
    s = s.replace(old, new, 1)
    p.write_text(s, encoding="utf-8", newline="\n")
    print("content.py OK")
else:
    print("content.py already patched")

# 2. api.py — cache + inject images into Results chapter
p = RR / "api.py"
s = p.read_text(encoding="utf-8").lstrip("\ufeff")

# 2a. add cache helpers
if "_cache_key" not in s:
    helper = '''

import hashlib
import json as _json


def _cache_key(sections):
    data = _json.dumps(
        [{"id": getattr(s, "id", ""), "title": getattr(s, "title", ""),
          "content": getattr(s, "content", "")} for s in sections],
        sort_keys=True, default=str,
    )
    return hashlib.sha256(data.encode()).hexdigest()[:16]


def _load_cache(project_root, key):
    if not project_root:
        return None
    f = Path(project_root) / ".report_cache" / f"{key}.json"
    if f.exists():
        try:
            return _json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


def _save_cache(project_root, key, sections):
    if not project_root:
        return
    try:
        d = Path(project_root) / ".report_cache"
        d.mkdir(exist_ok=True, parents=True)
        (d / f"{key}.json").write_text(_json.dumps(sections), encoding="utf-8")
    except Exception:
        pass
'''
    s = s.replace("def _facts_from_context(ctx):",
                  helper.lstrip() + "\n\ndef _facts_from_context(ctx):", 1)

# 2b. use cache in generate_report_pdf
old_ai = """        from . import ai_writer
        print("[AI] Generating sections...", flush=True)
        ai_sections = ai_writer.generate_sections(
            _facts_from_context(ctx),
            progress=lambda m: print(m, flush=True),
        )"""
new_ai = """        from . import ai_writer
        _key = _cache_key(sections)
        _cached = _load_cache(project_root, _key)
        if _cached:
            print(f"[AI] Using cached sections ({_key})", flush=True)
            ai_sections = _cached
        else:
            print(f"[AI] Generating sections ({_key})...", flush=True)
            ai_sections = ai_writer.generate_sections(
                _facts_from_context(ctx),
                progress=lambda m: print(m, flush=True),
            )
            _save_cache(project_root, _key, ai_sections)"""
if old_ai in s:
    s = s.replace(old_ai, new_ai, 1)

# 2c. inject images into Results chapter
old_img = """    imgs = (uploaded_imgs + disk_imgs)[:8]
    css_v = tokens_to_css_vars(d)"""
new_img = """    imgs = (uploaded_imgs + disk_imgs)[:8]
    if imgs:
        target = None
        for ch in chapters:
            if "result" in (ch.title or "").lower():
                target = ch
                break
        if target is None and chapters:
            target = chapters[-1]
        if target is not None:
            for i, img in enumerate(imgs, 1):
                target.blocks.append(Block(
                    type="figure",
                    text=f"Figure {i}: {img.caption}",
                    image_uri=img.data_uri,
                ))
            print(f"[IMG] Injected {len(imgs)} images into '{target.title}'", flush=True)
    imgs = []
    css_v = tokens_to_css_vars(d)"""
if old_img in s:
    s = s.replace(old_img, new_img, 1)

# ensure Block is imported
if "from .content import build_context, Section, _parse_blocks" in s:
    s = s.replace(
        "from .content import build_context, Section, _parse_blocks",
        "from .content import build_context, Section, _parse_blocks, Block", 1)

p.write_text(s, encoding="utf-8", newline="\n")
print("api.py OK")

# 3. base.html.j2 — remove gallery include
p = RR / "templates" / "base.html.j2"
s = p.read_text(encoding="utf-8")
s = s.replace('{% include "gallery.html.j2" %}\n', '', 1)
s = s.replace('{% include "gallery.html.j2" %}', '', 1)
p.write_text(s, encoding="utf-8", newline="\n")
print("base.html.j2 OK")

# 4. toc.html.j2 — remove gallery entry
p = RR / "templates" / "toc.html.j2"
s = p.read_text(encoding="utf-8")
s = s.replace('    <li><span class="toc-title">Project Image Gallery</span></li>\n', '', 1)
s = s.replace('    <li><span class="toc-title">Project Image Gallery</span></li>', '', 1)
p.write_text(s, encoding="utf-8", newline="\n")
print("toc.html.j2 OK")

# 5. chapter.html.j2 — handle figure block
p = RR / "templates" / "chapter.html.j2"
s = p.read_text(encoding="utf-8")
if 'block.type == "figure"' not in s:
    old_fig = '''      {% elif block.type == "table" %}'''
    new_fig = '''      {% elif block.type == "figure" %}
        <figure class="figure">
          <img src="{{ block.image_uri }}" alt="{{ block.text }}">
          <figcaption>{{ block.text }}</figcaption>
        </figure>
      {% elif block.type == "table" %}'''
    if old_fig in s:
        s = s.replace(old_fig, new_fig, 1)
p.write_text(s, encoding="utf-8", newline="\n")
print("chapter.html.j2 OK")

# 6. report.css — figure styles
p = RR / "styles" / "report.css"
b = p.read_bytes()
try:
    s = b.decode("utf-8")
except UnicodeDecodeError:
    s = b.decode("cp1252")

s += '''

/* Figures inside chapters */
figure.figure { margin: 16pt auto; text-align: center; page-break-inside: avoid; }
figure.figure img { max-width: 100%; max-height: 340pt; border: 0.75pt solid #333; padding: 4pt; }
figure.figure figcaption { font-size: 10pt; font-style: italic; margin-top: 6pt; color: #333; }
'''
p.write_text(s, encoding="utf-8", newline="\n")
print("report.css OK")
print("ALL DONE")
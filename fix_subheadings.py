from pathlib import Path
import re

RR = Path(r"D:\codeguard-ai-stage3\artifacts\codeguard-ai\backend\app\services\report_renderer")

# ========== 1. content.py: add level field to Section ==========
p = RR / "content.py"
s = p.read_text(encoding="utf-8").lstrip("\ufeff")

if "level: int = 1" not in s:
    old = '''@dataclass
class Section:
    title: str
    paragraphs: list = field(default_factory=list)
    blocks: list = field(default_factory=list)
    heading: str = None'''
    new = '''@dataclass
class Section:
    title: str
    paragraphs: list = field(default_factory=list)
    blocks: list = field(default_factory=list)
    heading: str = None
    level: int = 1'''
    if old in s:
        s = s.replace(old, new, 1)
        print("content.py: Section.level added")
    else:
        print("content.py: Section pattern not found")
else:
    print("content.py: Section already has level")

p.write_text(s, encoding="utf-8", newline="\n")

# ========== 2. ai_writer.py: mark subheadings with level=2 + propagate ==========
p = RR / "ai_writer.py"
s = p.read_text(encoding="utf-8").lstrip("\ufeff")

# Add level detection in _specs_from_headings
old = '''    for h in headings:
        title = (h.get("title") or "").strip()
        import re as _re
        # Strip ANY leading number (1., 5.1, 5.1.1) — renumber sequentially later
        clean = _re.sub(r"^\\d+(?:\\.\\d+)*\\.?\\s*", "", title).strip()
        if not clean:
            clean = title
'''
new = '''    for h in headings:
        title = (h.get("title") or "").strip()
        import re as _re
        # Detect subheading: number like 5.1 or 5.1.1
        is_sub = bool(_re.match(r"^\\d+\\.\\d+", title))
        # Strip ANY leading number
        clean = _re.sub(r"^\\d+(?:\\.\\d+)*\\.?\\s*", "", title).strip()
        if not clean:
            clean = title
'''
if old in s:
    s = s.replace(old, new, 1)
    print("ai_writer.py: sub detection added")

# Add level to the out.append dict
old2 = '''        out.append({
            "title": clean,
            "focus_keys": ["project_name", "project_type", "readme_summary",'''
new2 = '''        out.append({
            "title": clean,
            "level": 2 if is_sub else 1,
            "focus_keys": ["project_name", "project_type", "readme_summary",'''
if old2 in s:
    s = s.replace(old2, new2, 1)
    print("ai_writer.py: level passed to spec")

# Pass level through to output
old3 = '''        out.append({"title": title, "content": content})'''
new3 = '''        out.append({"title": title, "content": content, "level": spec.get("level", 1)})'''
if old3 in s:
    s = s.replace(old3, new3, 1)
    print("ai_writer.py: level passed to output")
else:
    # Try alternate
    m = re.search(r"out\.append\(\{\"title\": title, \"content\": content\}\)", s)
    if m:
        s = s[:m.start()] + 'out.append({"title": title, "content": content, "level": spec.get("level", 1)})' + s[m.end():]
        print("ai_writer.py: level passed to output (alt)")

p.write_text(s, encoding="utf-8", newline="\n")

# ========== 3. api.py: merge level-2 sections into previous chapter ==========
p = RR / "api.py"
s = p.read_text(encoding="utf-8").lstrip("\ufeff")

old4 = '''    chapters, ack, refs, abstract = [], None, None, None
    for item in ai_sections:
        title = (item.get("title") or "").strip()
        lower = title.lower()
        content = item.get("content", "")
        blocks = _parse_blocks(content)'''
new4 = '''    chapters, ack, refs, abstract = [], None, None, None
    for item in ai_sections:
        title = (item.get("title") or "").strip()
        lower = title.lower()
        content = item.get("content", "")
        level = item.get("level", 1)
        blocks = _parse_blocks(content)
        # Subheading: attach to previous chapter as h2 block + content
        if level == 2 and chapters:
            parent = chapters[-1]
            parent.blocks.append(Block(type="h2", text=title))
            parent.blocks.extend(blocks)
            continue'''
if old4 in s:
    s = s.replace(old4, new4, 1)
    print("api.py: subheading merge added")
else:
    print("api.py: merge pattern not found")

p.write_text(s, encoding="utf-8", newline="\n")

print("ALL DONE")
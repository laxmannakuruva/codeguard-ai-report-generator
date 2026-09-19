from pathlib import Path

# ---- content.py: unescape double-encoded entities ----
p = Path(r"D:\codeguard-ai-stage3\artifacts\codeguard-ai\backend\app\services\report_renderer\content.py")
s = p.read_text(encoding="utf-8")

if "html.unescape" not in s.split("def _clean")[1][:500]:
    s = s.replace(
        "import ast\nimport json\nimport re",
        "import ast\nimport html\nimport json\nimport re",
        1
    )
    # Add unescape inside _clean
    old_clean = '''def _clean(v):
    if v is None:
        return ""
    s = CONFLICT_RE.sub("", str(v))
    s = _strip_markdown(s)
    s = EMOJI_RE.sub("", s)
    return re.sub(r"[ \\t]+", " ", s).strip()'''
    new_clean = '''def _clean(v):
    if v is None:
        return ""
    s = CONFLICT_RE.sub("", str(v))
    s = html.unescape(html.unescape(html.unescape(s)))
    s = _strip_markdown(s)
    s = EMOJI_RE.sub("", s)
    return re.sub(r"[ \\t]+", " ", s).strip()'''
    if old_clean in s:
        s = s.replace(old_clean, new_clean, 1)
        print("content.py: unescape added")
    else:
        print("content.py: _clean pattern not found")
else:
    print("content.py: already has unescape")

p.write_text(s, encoding="utf-8", newline="\n")

# ---- chapter template: remove stray numbering at start ----
p = Path(r"D:\codeguard-ai-stage3\artifacts\codeguard-ai\backend\app\services\report_renderer\templates\chapter.html.j2")
s = p.read_text(encoding="utf-8")
if "block.text" in s and "lstrip" not in s:
    # strip leading "N " or "N. " from paragraph text at render time
    s = s.replace(
        '<p>{{ block.text }}</p>',
        '<p>{{ block.text.lstrip("0123456789. ") if block.text[:2].strip().rstrip(".").isdigit() else block.text }}</p>',
        1
    )
    p.write_text(s, encoding="utf-8", newline="\n")
    print("chapter.html.j2: stray number stripper added")

# ---- report.css: ensure abstract has spacing ----
p = Path(r"D:\codeguard-ai-stage3\artifacts\codeguard-ai\backend\app\services\report_renderer\styles\report.css")
s = p.read_text(encoding="utf-8")
if "abstract-heading-space" not in s:
    s += '''

/* abstract-heading-space */
.page.front h1 {
  display: block !important;
  margin: 0 0 16pt 0 !important;
}
'''
    p.write_text(s, encoding="utf-8", newline="\n")
    print("report.css: heading spacing added")

print("ALL DONE")
from pathlib import Path

B = Path(r"D:\codeguard-ai-stage3\artifacts\codeguard-ai\backend")
RR = B / "app" / "services" / "report_renderer"

# ---- api.py: extract Abstract separately, skip page measurement ----
p = RR / "api.py"
s = p.read_text(encoding="utf-8").lstrip("\ufeff")

old = """    chapters, ack, refs = [], None, None
    for item in ai_sections:
        title = (item.get("title") or "").strip()
        lower = title.lower()
        content = item.get("content", "")
        blocks = _parse_blocks(content)
        paragraphs = [b.text for b in blocks if b.type == "p"]
        section = Section(title=title, paragraphs=paragraphs, blocks=blocks)
        if lower == "acknowledgement":
            ack = section
        elif lower == "references":
            refs = section
        else:
            chapters.append(section)
    for i, ch in enumerate(chapters, 1):
        ch.heading = f"{i}. {ch.title}"
    return chapters, ack, refs"""
new = """    chapters, ack, refs, abstract = [], None, None, None
    for item in ai_sections:
        title = (item.get("title") or "").strip()
        lower = title.lower()
        content = item.get("content", "")
        blocks = _parse_blocks(content)
        paragraphs = [b.text for b in blocks if b.type == "p"]
        section = Section(title=title, paragraphs=paragraphs, blocks=blocks)
        if lower == "acknowledgement":
            ack = section
        elif lower == "references":
            refs = section
        elif lower == "abstract":
            abstract = section
        else:
            chapters.append(section)
    for i, ch in enumerate(chapters, 2):
        ch.heading = f"{i}. {ch.title}"
    return chapters, ack, refs, abstract"""
if old in s:
    s = s.replace(old, new, 1)

old2 = """        chapters, ack, refs = _ai_to_chapters(ai_sections)
        ctx["chapters"] = chapters
        ctx["acknowledgement"] = ack
        ctx["references_section"] = refs
        print(f"[AI] {len(chapters)} chapters | ack={bool(ack)} | refs={bool(refs)}", flush=True)"""
new2 = """        chapters, ack, refs, abstract = _ai_to_chapters(ai_sections)
        ctx["chapters"] = chapters
        ctx["acknowledgement"] = ack
        ctx["references_section"] = refs
        ctx["abstract"] = abstract
        print(f"[AI] {len(chapters)} chapters | ack={bool(ack)} | refs={bool(refs)} | abstract={bool(abstract)}", flush=True)"""
if old2 in s:
    s = s.replace(old2, new2, 1)

# Skip page measurement entirely - return single pass
old3 = """    page_numbers = {}
    try:
        page_numbers = _measure_pages_from_pdf(pdf_pass1, chapters)
        print(f"[TOC] page numbers: {page_numbers}", flush=True)
    except Exception as e:
        log.warning("PDF measurement failed: %s", e)

    html_pass2 = _inject(html_pass1, page_numbers)
    return _render_pdf(html_pass2)"""
new3 = """    return pdf_pass1"""
if old3 in s:
    s = s.replace(old3, new3, 1)

p.write_text(s, encoding="utf-8", newline="\n")
print("api.py OK")

# ---- base.html.j2: reorder ----
p = RR / "templates" / "base.html.j2"
s = p.read_text(encoding="utf-8")
new_base = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{{ ctx.project_name }} - Project Report</title>
<style>
{{ css_vars }}

{{ css_body }}
</style>
</head>
<body>

{% include "cover.html.j2" %}
{% include "front_matter.html.j2" %}
{% include "abstract.html.j2" %}
{% include "toc.html.j2" %}
{% include "chapter.html.j2" %}
{% include "back_matter.html.j2" %}
{% include "gallery.html.j2" %}

</body>
</html>
'''
p.write_text(new_base, encoding="utf-8", newline="\n")
print("base.html.j2 OK")

# ---- abstract.html.j2 (new) ----
p = RR / "templates" / "abstract.html.j2"
p.write_text('''<section class="page front" id="anchor-abstract">
  <h1>Abstract</h1>
  <div class="rule"></div>
  {% if ctx.abstract and ctx.abstract.blocks %}
    {% for block in ctx.abstract.blocks %}
      {% if block.type == "p" %}<p>{{ block.text }}</p>
      {% elif block.type == "ul" %}<ul>{% for item in block.items %}<li>{{ item }}</li>{% endfor %}</ul>
      {% elif block.type == "ol" %}<ol>{% for item in block.items %}<li>{{ item }}</li>{% endfor %}</ol>
      {% endif %}
    {% endfor %}
  {% else %}
    <p class="notice">Abstract content is not available.</p>
  {% endif %}
</section>
''', encoding="utf-8", newline="\n")
print("abstract.html.j2 OK")

# ---- toc.html.j2: no page numbers, no dots ----
p = RR / "templates" / "toc.html.j2"
p.write_text('''<section class="page front" id="anchor-toc">
  <h1>Table of Contents</h1>
  <div class="rule"></div>

  <ul class="toc-list">
    <li><span class="toc-title">Acknowledgement</span></li>
    <li><span class="toc-title">Abstract</span></li>

    {% for ch in ctx.chapters %}
    <li><span class="toc-title">{{ ch.heading }}</span></li>
    {% endfor %}

    <li><span class="toc-title">Project Image Gallery</span></li>
    <li><span class="toc-title">Appendices</span></li>
    <li><span class="toc-title">References</span></li>
  </ul>
</section>
''', encoding="utf-8", newline="\n")
print("toc.html.j2 OK")

# ---- report.css: TOC + gallery, kill page numbers ----
p = RR / "styles" / "report.css"
b = p.read_bytes()
try:
    s = b.decode("utf-8")
except UnicodeDecodeError:
    s = b.decode("cp1252")

s += '''

/* Kill all page numbers */
@page { @top-left { content: none !important; } @top-center { content: none !important; }
        @top-right { content: none !important; } @bottom-left { content: none !important; }
        @bottom-center { content: none !important; } @bottom-right { content: none !important; } }

/* TOC plain list */
.toc-list { list-style: none !important; padding: 0 !important; margin: 12pt 0 0 0 !important; }
.toc-list li { display: block !important; margin: 8pt 0 !important; padding: 0 !important; }
.toc-list .toc-title { font-weight: 600; }
.toc-list .toc-page, .toc-list .toc-dots { display: none !important; }

/* Gallery */
.gallery { display: block; margin-top: 12pt; }
.gallery-item { display: block; page-break-inside: avoid; margin: 14pt 0; text-align: center; }
.gallery-item img { max-width: 100%; max-height: 340pt; border: 0.75pt solid #333; padding: 4pt; }
.gallery-item figcaption { font-size: 10pt; font-style: italic; margin-top: 6pt; color: #333; }
'''
p.write_text(s, encoding="utf-8", newline="\n")
print("report.css OK")

# ---- content.py: strip root from paths + tree ----
p = RR / "content.py"
s = p.read_text(encoding="utf-8")

if "_shorten_paths" not in s:
    helper = '''

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
'''
    s = s.replace("def _join(items, sep=\", \"):", helper.lstrip() + "\n\ndef _join(items, sep=\", \"):", 1)

old_ret = '''    return {
        "project_name": escape(pn),'''
new_ret = '''    eps_short = _shorten_paths(eps)
    imp_short = _shorten_paths(imp)
    fold_short = _shorten_paths(fold)

    return {
        "folder_tree": _render_tree(fold_short),
        "project_name": escape(pn),'''
if old_ret in s and '"folder_tree"' not in s:
    s = s.replace(old_ret, new_ret, 1)

# override the entry_points/important_files values with the shortened versions
s = s.replace('"entry_points": eps,', '"entry_points": eps_short,', 1)
s = s.replace('"important_files": imp,', '"important_files": imp_short,', 1)

p.write_text(s, encoding="utf-8", newline="\n")
print("content.py OK")

# ---- back_matter.html.j2: use folder_tree ----
p = RR / "templates" / "back_matter.html.j2"
s = p.read_text(encoding="utf-8")
s = s.replace(
    '{% if ctx.folder_structure and ctx.folder_structure|length > 0 %}',
    '{% if ctx.folder_tree and ctx.folder_tree|length > 0 %}', 1)
s = s.replace(
    '<pre class="tree">{% for line in ctx.folder_structure %}{{ line }}\n{% endfor %}</pre>',
    '<pre class="tree">{% for line in ctx.folder_tree %}{{ line }}\n{% endfor %}</pre>', 1)
p.write_text(s, encoding="utf-8", newline="\n")
print("back_matter.html.j2 OK")

print("ALL DONE")
from pathlib import Path

RR = Path(r"D:\codeguard-ai-stage3\artifacts\codeguard-ai\backend\app\services\report_renderer")

# ---------- 1. pdf_structure.py — skip only cover+cert+TOC ----------
p = RR / "pdf_structure.py"
s = p.read_text(encoding="utf-8")
old = '''    start_page = None
    for l in lines:
        if toc_page and l["page"] <= toc_page:
            continue
        if re.match(r"^1\\.\\s+[A-Z]", l["text"]) and l["size"] >= body_size + 1:
            start_page = l["page"]
            break
    if start_page is None:
        start_page = (toc_page or 2) + 1'''
new = '''    # Skip cover (p1), certificate (p2), TOC page — keep everything else
    skip_pages = {1, 2}
    if toc_page:
        skip_pages.add(toc_page)
    start_page = 3'''
if old in s:
    s = s.replace(old, new, 1)
    print("pdf_structure.py: skip logic fixed")
else:
    print("pdf_structure.py: pattern NOT found (may already be fixed)")
# Also change the page filter from < start_page to in skip_pages
s = s.replace('        if l["page"] < start_page:\n            continue\n        if toc_page and l["page"] == toc_page:\n            continue',
              '        if l["page"] in skip_pages:\n            continue', 1)
p.write_text(s, encoding="utf-8", newline="\n")

# ---------- 2. content.py — double-unescape ----------
p = RR / "content.py"
s = p.read_text(encoding="utf-8")
if "import html" not in s:
    s = s.replace("import ast\nimport json\nimport re",
                  "import ast\nimport html\nimport json\nimport re", 1)
    print("content.py: html imported")
if "html.unescape" not in s:
    s = s.replace('s = CONFLICT_RE.sub("", str(v))',
                  's = CONFLICT_RE.sub("", str(v))\n    s = html.unescape(html.unescape(html.unescape(s)))', 1)
    print("content.py: unescape added")
else:
    print("content.py: already unescapes")
p.write_text(s, encoding="utf-8", newline="\n")

# ---------- 3. ai_writer.py — prepend Ack + Abstract ----------
p = RR / "ai_writer.py"
s = p.read_text(encoding="utf-8")
if "acknowledg" not in s.split("_specs_from_headings")[1][:800] if "_specs_from_headings" in s else False:
    pass
old = '''    if not headings or len(headings) < 5:
        return None
    out = []'''
new = '''    if not headings or len(headings) < 5:
        return None
    out = []
    titles_lower = " ".join((h.get("title") or "").lower() for h in headings)
    if "acknowledg" not in titles_lower:
        out.append({
            "title": "Acknowledgement",
            "focus_keys": ["project_name"],
            "instruction": ("Write 200-250 words of formal academic acknowledgement. "
                            "Thank the institution, project guide, and collaborators generically. "
                            "Warm academic tone."),
        })
    if "abstract" not in titles_lower:
        out.append({
            "title": "Abstract",
            "focus_keys": ["project_name", "project_type", "readme_summary",
                           "languages", "frameworks", "libraries", "features"],
            "instruction": ("Write a formal abstract of 200-280 words. Cover what the project "
                            "is, what problem it solves, technologies used, what it produces, "
                            "and main outcome."),
        })'''
if old in s:
    s = s.replace(old, new, 1)
    print("ai_writer.py: ack+abstract prepend added")
p.write_text(s, encoding="utf-8", newline="\n")

# ---------- 4. api.py — robust title matching ----------
p = RR / "api.py"
s = p.read_text(encoding="utf-8").lstrip("\ufeff")
old = '''        if lower == "acknowledgement":
            ack = section
        elif lower == "references":
            refs = section
        elif lower == "abstract":
            abstract = section
        else:
            chapters.append(section)'''
new = '''        norm = lower.strip().rstrip(":").rstrip(".")
        ack_names = {"acknowledgement", "acknowledgements", "acknowledgment", "acknowledgments"}
        refs_names = {"references", "reference", "bibliography"}
        abs_names = {"abstract", "summary"}
        skip_names = {"appendices", "appendix", "table of contents", "contents"}
        if norm in ack_names:
            ack = section
        elif norm in refs_names:
            refs = section
        elif norm in abs_names:
            abstract = section
        elif norm in skip_names:
            pass
        else:
            chapters.append(section)'''
if old in s:
    s = s.replace(old, new, 1)
    print("api.py: matching updated")
else:
    print("api.py: matching already updated")
p.write_text(s, encoding="utf-8", newline="\n")

# ---------- 5. toc.html.j2 — rewrite (always) ----------
(RR / "templates" / "toc.html.j2").write_text('''<section class="page front" id="anchor-toc">
  <h1>Table of Contents</h1>
  <div class="rule"></div>

  <ul class="toc-list">
    <li><span class="toc-title">Acknowledgement</span></li>
    <li><span class="toc-title">Abstract</span></li>

    {% for ch in ctx.chapters %}
    <li><span class="toc-title">{{ ch.heading }}</span></li>
    {% endfor %}

    <li><span class="toc-title">{{ ctx.chapters|length + 1 }}. Appendices</span></li>
    <li><span class="toc-title">{{ ctx.chapters|length + 2 }}. References</span></li>
  </ul>
</section>
''', encoding="utf-8", newline="\n")
print("toc.html.j2 rewritten")

# ---------- 6. report.css — TOC block display ----------
p = RR / "styles" / "report.css"
s = p.read_text(encoding="utf-8")
if "TOC FINAL FIX" not in s:
    s += '''

/* TOC FINAL FIX */
.toc-list { list-style: none !important; padding: 0 !important; margin: 12pt 0 0 0 !important; }
.toc-list li {
  display: block !important;
  margin: 6pt 0 !important;
  padding: 0 !important;
  width: 100% !important;
  clear: both !important;
}
.toc-list .toc-title { display: inline !important; font-weight: 600 !important; font-size: 11.5pt !important; }
'''
    print("report.css: TOC block rule added")
p.write_text(s, encoding="utf-8", newline="\n")

print("ALL DONE")
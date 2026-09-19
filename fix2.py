from pathlib import Path

R = Path(r"D:\codeguard-ai-stage3\artifacts\codeguard-ai\backend\app\services\report_renderer")

# ---------- content.py: fix table separator + remove figures ----------
p = R / "content.py"
s = p.read_text(encoding="utf-8")

old = """        m_heading = MD_HEADING_LINE_RE.match(line)
        m_figure = MD_FIGURE_RE.match(line)
        m_table_row = MD_TABLE_ROW_RE.match(line)
        m_table_sep = MD_TABLE_SEP_RE.match(line)

        if m_table_row:
            flush_paragraph()
            flush_list()
            cells = [c.strip() for c in m_table_row.group(1).split("|")]
            table_rows.append(cells)
            continue

        if m_table_sep:
            continue
"""
new = """        m_heading = MD_HEADING_LINE_RE.match(line)
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
"""
if old in s:
    s = s.replace(old, new, 1)
    print("content.py: separator fix OK")
else:
    print("content.py: separator block already fixed or missing")

old2 = """        if m_figure:
            flush_table()
            flush_paragraph()
            flush_list()
            blocks.append(Block(type="figure", text=_clean(m_figure.group(1))))
            continue
"""
new2 = """        if m_figure:
            continue
"""
if old2 in s:
    s = s.replace(old2, new2, 1)
    print("content.py: figures removed OK")
else:
    print("content.py: figure block already removed")

p.write_text(s, encoding="utf-8", newline="\n")

# ---------- report.css: clean subheadings + hide figures ----------
p = R / "styles" / "report.css"
b = p.read_bytes()
try:
    s = b.decode("utf-8")
except UnicodeDecodeError:
    s = b.decode("cp1252")

old3 = """.chapter h2.subheading {
  font-size: 13pt;
  margin: 18pt 0 8pt 0;
  border-bottom: 0.5pt solid #999;
  padding-bottom: 3pt;
  page-break-after: avoid;
}"""
new3 = """.chapter h2.subheading {
  font-size: 11.5pt;
  font-weight: 700;
  margin: 14pt 0 6pt 0;
  padding: 0;
  border: none;
  page-break-after: avoid;
}"""
if old3 in s:
    s = s.replace(old3, new3, 1)
    print("report.css: subheading cleaned OK")
else:
    print("report.css: subheading already clean")

old4 = """figure.figure { margin: 16pt auto; text-align: center; page-break-inside: avoid; }"""
new4 = """figure.figure { display: none !important; }"""
if old4 in s:
    s = s.replace(old4, new4, 1)
    print("report.css: figures hidden OK")

p.write_text(s, encoding="utf-8", newline="\n")

# ---------- ai_writer.py: remove FIGURE instruction, strip emoji ----------
p = R / "ai_writer.py"
s = p.read_text(encoding="utf-8")

s = s.replace(
    '        "Include [FIGURE: caption] placeholders where a diagram would help. "\n',
    ""
)

old5 = """        "7. When it helps, include ONE figure placeholder on its own line:\\n"
        "   [FIGURE: short caption]\\n\""""
if old5 in s:
    s = s.replace(old5, "", 1)
    s = s.replace('"8. Do NOT start with', '"7. Do NOT start with', 1)
    s = s.replace('"9. Vary your opening', '"8. Vary your opening', 1)
    s = s.replace('"10. For the Conclusions', '"9. For the Conclusions', 1)
    s = s.replace('"11. For the References', '"10. For the References', 1)
    s = s.replace('"12. For lists of features', '"11. For lists of features', 1)
    print("ai_writer.py: FIGURE rule removed")

s = s.replace(
    '        "Never output apologies or disclaimers."',
    '        "Never output apologies or disclaimers. "\n'
    '        "Never use emoji or icon characters."'
)

p.write_text(s, encoding="utf-8", newline="\n")
print("ai_writer.py OK")

print("ALL DONE")
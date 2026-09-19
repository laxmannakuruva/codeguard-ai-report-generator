from pathlib import Path

R = Path(r"D:\codeguard-ai-stage3\artifacts\codeguard-ai\backend\app\services\report_renderer")

def read(p):
    with open(p, "r", encoding="utf-8") as f:
        return f.read()

def write(p, s):
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(s)

# ---------------- ai_writer.py ----------------
p = R / "ai_writer.py"
s = read(p)

old = '"You write formal, detailed paragraphs for internship reports. "'
new = ('"You write formal, structured internship report sections. "\n'
       '        "Structure long sections with \'## Subheading\' lines. "\n'
       '        "Include markdown tables (| col | col |) where useful. "\n'
       '        "Include [FIGURE: caption] placeholders where a diagram would help. "\n'
       '        "Break long text into 2-4 sentence paragraphs. "')
assert old in s, "system_prompt not found"
s = s.replace(old, new, 1)

old4 = '"4. Write in flowing academic prose. No markdown syntax.\\n"'
new4 = ('"4. Structure long sections with subheadings on their own line: \'## Subheading\'.\\n"\n'
        '        "5. Break text into short paragraphs (2-4 sentences). Never write walls of text.\\n"\n'
        '        "6. When it helps, include ONE markdown table with a header and body rows:\\n"\n'
        '        "   | Column A | Column B |\\n"\n'
        '        "   | Value 1  | Value 2  |\\n"\n'
        '        "7. When it helps, include ONE figure placeholder on its own line:\\n"\n'
        '        "   [FIGURE: short caption]\\n"')
assert old4 in s, "_build_prompt rule 4 not found"
s = s.replace(old4, new4, 1)

s = s.replace('"5. Do NOT start with', '"8. Do NOT start with', 1)
s = s.replace('"6. Vary your opening', '"9. Vary your opening', 1)
s = s.replace('"7. For the Conclusions', '"10. For the Conclusions', 1)
s = s.replace('"8. For the References', '"11. For the References', 1)
s = s.replace('"9. For lists of features', '"12. For lists of features', 1)
s = s.replace('"Return ONLY the paragraph body. No heading. No commentary."',
              '"Return ONLY the section body. No top-level title. Use ## for subheadings."', 1)
write(p, s)
print("ai_writer.py OK")

# ---------------- content.py ----------------
p = R / "content.py"
s = read(p)

old_anchor = 'MD_HEADING_RE = re.compile(r"^#{1,6}\\s+", re.MULTILINE)'
new_anchor = (old_anchor + '\n'
              'MD_HEADING_LINE_RE = re.compile(r"^\\s*#{1,6}\\s+(.+)$")\n'
              'MD_TABLE_ROW_RE = re.compile(r"^\\s*\\|(.+)\\|\\s*$")\n'
              'MD_TABLE_SEP_RE = re.compile(r"^\\s*\\|[\\s\\-:|]+\\|\\s*$")\n'
              'MD_FIGURE_RE = re.compile(r"^\\s*\\[FIGURE:\\s*(.+?)\\]\\s*$", re.IGNORECASE)')
assert old_anchor in s, "regex anchor not found"
s = s.replace(old_anchor, new_anchor, 1)

old_vars = '''    ol_items = []
    ul_items = []

    def flush_paragraph():'''
new_vars = '''    ol_items = []
    ul_items = []
    table_rows = []

    def flush_table():
        nonlocal table_rows
        if table_rows:
            rows = [[_clean(c) for c in row] for row in table_rows]
            rows = [r for r in rows if any(r)]
            if rows:
                blocks.append(Block(type="table", items=rows))
            table_rows = []

    def flush_paragraph():'''
assert old_vars in s, "vars block not found"
s = s.replace(old_vars, new_vars, 1)

old_disp = '''        m_num = NUMBERED_LINE_RE.match(line)
        m_bul = BULLET_LINE_RE.match(line)

        if m_num:'''
new_disp = '''        m_heading = MD_HEADING_LINE_RE.match(line)
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

        if m_heading:
            flush_table()
            flush_paragraph()
            flush_list()
            blocks.append(Block(type="h2", text=_clean(m_heading.group(1))))
            continue

        if m_figure:
            flush_table()
            flush_paragraph()
            flush_list()
            blocks.append(Block(type="figure", text=_clean(m_figure.group(1))))
            continue

        flush_table()

        m_num = NUMBERED_LINE_RE.match(line)
        m_bul = BULLET_LINE_RE.match(line)

        if m_num:'''
assert old_disp in s, "dispatch block not found"
s = s.replace(old_disp, new_disp, 1)

old_end = '''    flush_paragraph()
    flush_list()
    return blocks'''
new_end = '''    flush_table()
    flush_paragraph()
    flush_list()
    return blocks'''
assert old_end in s, "end block not found"
s = s.replace(old_end, new_end, 1)
write(p, s)
print("content.py OK")

# ---------------- report.css ----------------
p = R / "styles" / "report.css"
s = read(p)
if ".figure-placeholder" not in s:
    s += '''

/* subheadings inside chapters */
.chapter h2.subheading {
  font-size: 13pt;
  margin: 18pt 0 8pt 0;
  border-bottom: 0.5pt solid #999;
  padding-bottom: 3pt;
  page-break-after: avoid;
}

/* figure placeholder */
figure.figure { margin: 16pt auto; text-align: center; page-break-inside: avoid; }
figure.figure .figure-placeholder {
  border: 1pt dashed #888; padding: 24pt 12pt; background: #fafafa;
  font-family: Consolas, monospace; font-size: 10pt; color: #666;
}
figure.figure figcaption { font-size: 9.5pt; font-style: italic; margin-top: 6pt; }
'''
    write(p, s)
    print("report.css OK")
else:
    print("report.css already patched")

print("ALL DONE")
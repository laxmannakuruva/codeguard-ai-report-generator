from pathlib import Path
import re

R = Path(r"D:\codeguard-ai-stage3\artifacts\codeguard-ai\backend\app\services\report_renderer")

# ========== content.py ==========
p = R / "content.py"
s = p.read_text(encoding="utf-8")

# 1. add EMOJI_RE after the FIGURE regex
if "EMOJI_RE" not in s:
    anchor = 'MD_FIGURE_RE = re.compile(r"^\\s*\\[FIGURE:\\s*(.+?)\\]\\s*$", re.IGNORECASE)'
    add = anchor + '\nEMOJI_RE = re.compile(\n    "["\n    "\\U0001F300-\\U0001F9FF"\n    "\\U00002600-\\U000027BF"\n    "\\U0001F000-\\U0001F0FF"\n    "\\U0001F900-\\U0001F9FF"\n    "\\u2600-\\u27BF"\n    "\\u2190-\\u21FF"\n    "\\u2B00-\\u2BFF"\n    "\\uFE00-\\uFE0F"\n    "\\u200D"\n    "]+",\n    flags=re.UNICODE,\n)'
    s = s.replace(anchor, add, 1)

# 2. strip emoji inside _clean
old = 'return re.sub(r"[ \\t]+", " ", s).strip()'
new = 's = EMOJI_RE.sub("", s)\n    return re.sub(r"[ \\t]+", " ", s).strip()'
if old in s and 'EMOJI_RE.sub("", s)' not in s:
    s = s.replace(old, new, 1)

# 3. looser table separator regex (handles no-pipe dashes)
old_sep = 'MD_TABLE_SEP_RE = re.compile(r"^\\s*\\|[\\s\\-:|]+\\|\\s*$")'
new_sep = 'MD_TABLE_SEP_RE = re.compile(r"^\\s*[\\|\\s\\-:]*-{3,}[\\|\\s\\-:]*$")'
if old_sep in s:
    s = s.replace(old_sep, new_sep, 1)

# 4. track last heading so we can strip duplicates
old_vars = '    table_rows = []'
new_vars = '    table_rows = []\n    last_heading = [None]'
if 'last_heading = [None]' not in s:
    s = s.replace(old_vars, new_vars, 1)

# 5. strip duplicate heading in flush_paragraph
old_flush = '''    def flush_paragraph():
        if buffer:
            joined = " ".join(l.strip() for l in buffer if l.strip())
            joined = _clean(joined)
            if joined:
                blocks.append(Block(type="p", text=joined))
            buffer.clear()'''
new_flush = '''    def flush_paragraph():
        if buffer:
            joined = " ".join(l.strip() for l in buffer if l.strip())
            joined = _clean(joined)
            h = last_heading[0]
            if h and joined and joined.startswith(h):
                joined = joined[len(h):].lstrip(":.").strip()
            if joined:
                blocks.append(Block(type="p", text=joined))
            buffer.clear()
            last_heading[0] = None'''
if old_flush in s:
    s = s.replace(old_flush, new_flush, 1)

# 6. handle heading+content on same line, and set last_heading
old_h2 = '''            htext = _clean(m_heading.group(1))
            blocks.append(Block(type="h2", text=htext))
            last_heading[0] = htext
            continue'''
if old_h2 not in s:
    old_h2 = '''            blocks.append(Block(type="h2", text=_clean(m_heading.group(1))))
            continue'''
new_h2 = '''            raw_h = m_heading.group(1).strip()
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
            continue'''
if old_h2 in s:
    s = s.replace(old_h2, new_h2, 1)

p.write_text(s, encoding="utf-8", newline="\n")
print("content.py OK")

# ========== ai_writer.py ==========
p = R / "ai_writer.py"
s = p.read_text(encoding="utf-8")

# stronger anti-emoji + anti-repeat in system prompt
old_sp = '"Never use emoji or icon characters."'
new_sp = ('"Never use emoji, pin symbols (like the pushpin icon), or any unicode icon. "\n'
          '        "Never repeat the subheading text at the start of a paragraph."')
if old_sp in s:
    s = s.replace(old_sp, new_sp, 1)
elif 'Never use emoji, pin symbols' not in s:
    s = s.replace('"Never output apologies or disclaimers."',
                  '"Never output apologies or disclaimers. "\n'
                  '        "Never use emoji, pin symbols, or unicode icons. "\n'
                  '        "Never repeat the subheading text at the start of a paragraph."', 1)

# add rules 12 & 13 in _build_prompt
anchor = '"   starting with \'- \'.\\n\\n"'
add = ('"   starting with \'- \'.\\n"\n'
       '        "12. NEVER use emoji, pin symbols (like the pushpin), or unicode icons.\\n"\n'
       '        "13. After a \'## Subheading\' line, do NOT repeat the subheading text\\n"\n'
       '        "    at the start of the next paragraph.\\n\\n"')
if '12. NEVER use emoji' not in s and anchor in s:
    s = s.replace(anchor, add, 1)

p.write_text(s, encoding="utf-8", newline="\n")
print("ai_writer.py OK")

# ========== report.css ==========
p = R / "styles" / "report.css"
b = p.read_bytes()
try:
    s = b.decode("utf-8")
except UnicodeDecodeError:
    s = b.decode("cp1252")

old_css = """.chapter h2.subheading {
  font-size: 11.5pt;
  font-weight: 700;
  margin: 14pt 0 6pt 0;
  padding: 0;
  border: none;
  page-break-after: avoid;
}"""
new_css = """.chapter h2.subheading {
  font-size: 12pt;
  font-weight: 700;
  margin: 16pt 0 6pt 0;
  padding: 0;
  border: none;
  page-break-after: avoid;
  color: #000;
}"""
if old_css in s:
    s = s.replace(old_css, new_css, 1)
    print("report.css OK")
else:
    print("report.css: pattern already clean or missing")

p.write_text(s, encoding="utf-8", newline="\n")
print("ALL DONE")
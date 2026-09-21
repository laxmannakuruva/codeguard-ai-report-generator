from pathlib import Path
import re

RR = Path(r"D:\codeguard-ai-stage3\artifacts\codeguard-ai\backend\app\services\report_renderer")

# ========== 1. ai_writer.py: revert "keep subheadings" — strip all numbers ==========
p = RR / "ai_writer.py"
s = p.read_text(encoding="utf-8").lstrip("\ufeff")

old = '''    for h in headings:
        title = (h.get("title") or "").strip()
        import re as _re
        # If it is a subheading (5.1, 5.2), keep the full title as-is
        if _re.match(r"^\\d+\\.\\d+", title):
            clean = title
        else:
            clean = _re.sub(r"^\\d+\\.?\\s+", "", title).strip()
            if not clean:
                clean = title
'''

new = '''    for h in headings:
        title = (h.get("title") or "").strip()
        import re as _re
        # Strip ANY leading number (1., 5.1, 5.1.1) — renumber sequentially later
        clean = _re.sub(r"^\\d+(?:\\.\\d+)*\\.?\\s*", "", title).strip()
        if not clean:
            clean = title
'''

if old in s:
    s = s.replace(old, new, 1)
    print("ai_writer.py: strip-all-numbers reverted")
else:
    print("ai_writer.py: pattern NOT found")

# ========== 2. ai_writer.py: roman fix for I/1 ==========
if "ROMAN_FIX_APPLY" not in s:
    # Find the system_prompt and add a post-processing step
    old2 = '''def generate_sections(facts, progress=None, custom_headings=None):
    specs_to_use = _specs_from_headings(custom_headings) if custom_headings else None'''
    new2 = '''def _roman_fix(text):
    """ROMAN_FIX_APPLY: fix '1 would like' -> 'I would like'."""
    import re as _re
    # After sentence break or start
    text = _re.sub(r"(^|[.!?]\\s+)1\\s+(would|am|have|had|will|was|wish|extend|express|sincerely|thank|acknowledge)", r"\\1I \\2", text)
    # Anywhere else: " 1 " at start of a word followed by verb
    text = _re.sub(r"\\b1\\s+(would|am|have|had|wish|extend|express|acknowledge)", r"I \\1", text)
    return text


def generate_sections(facts, progress=None, custom_headings=None):
    specs_to_use = _specs_from_headings(custom_headings) if custom_headings else None'''
    if old2 in s:
        s = s.replace(old2, new2, 1)
        print("ai_writer.py: _roman_fix added")
    else:
        print("ai_writer.py: generate_sections anchor not found")

    # Apply fix in the loop
    old3 = '''        if not content:
            content = "[AI returned empty content]"'''
    new3 = '''        if not content:
            content = "[AI returned empty content]"
        content = _roman_fix(content)'''
    if old3 in s:
        s = s.replace(old3, new3, 1)
        print("ai_writer.py: _roman_fix applied in loop")

p.write_text(s, encoding="utf-8", newline="\n")

# ========== 3. content.py: force unescape on chapter text ==========
p = RR / "content.py"
s = p.read_text(encoding="utf-8").lstrip("\ufeff")
if "FORCE_UNESCAPE" not in s:
    old4 = '''def _clean(v):
    if v is None:
        return ""'''
    new4 = '''def _clean(v):
    """FORCE_UNESCAPE: always triple-unescape HTML entities."""
    if v is None:
        return ""'''
    if old4 in s:
        s = s.replace(old4, new4, 1)
    # Ensure unescape line runs even on chapter content
    if "html.unescape(html.unescape(html.unescape(s)))" not in s:
        s = s.replace(
            "s = CONFLICT_RE.sub(\"\", str(v))",
            "s = CONFLICT_RE.sub(\"\", str(v))\n    s = html.unescape(html.unescape(html.unescape(s)))",
            1
        )
        print("content.py: triple-unescape added")

p.write_text(s, encoding="utf-8", newline="\n")
print("content.py saved")

# ========== 4. api.py: apply _clean to chapter content before render ==========
p = RR / "api.py"
s = p.read_text(encoding="utf-8").lstrip("\ufeff")
if "APPLY_CLEAN_TO_BLOCKS" not in s:
    old5 = '''        blocks = _parse_blocks(content)
        paragraphs = [b.text for b in blocks if b.type == "p"]'''
    new5 = '''        blocks = _parse_blocks(content)
        # APPLY_CLEAN_TO_BLOCKS: force unescape one more time on all text
        from .content import _clean as _clean_fn
        for _b in blocks:
            if _b.text:
                _b.text = _clean_fn(_b.text)
            if _b.items:
                _b.items = [_clean_fn(i) for i in _b.items]
        paragraphs = [b.text for b in blocks if b.type == "p"]'''
    if old5 in s:
        s = s.replace(old5, new5, 1)
        print("api.py: force-clean on blocks")
    else:
        print("api.py: _parse_blocks pattern not found")

p.write_text(s, encoding="utf-8", newline="\n")

print("ALL DONE")
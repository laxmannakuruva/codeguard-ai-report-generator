from pathlib import Path
p = Path(r"D:\codeguard-ai-stage3\artifacts\codeguard-ai\backend\app\services\report_renderer\pdf_structure.py")
s = p.read_text(encoding="utf-8").lstrip("\ufeff")

# Insert _bad_pages computation BEFORE "toc_page = _find_toc_page(lines)"
old = '''    toc_page = _find_toc_page(lines)

    # Find the first page where a real numbered chapter "1. X" begins'''

new = '''    # --- Rule 1: cert/ack page filter ---
    _cert_keywords = (
        "certificate", "certify", "signature of", "signature:",
        "gratitude", "thank you", "dean of", "vice chancellor",
        "joining report", "we would like", "i would like",
        "sincerely", "acknowledgement", "acknowledgment",
    )
    from collections import defaultdict as _dd
    _page_text = _dd(str)
    for _l in lines:
        _page_text[_l["page"]] += " " + _l["text"].lower()
    _bad_pages = set()
    for _pg, _txt in _page_text.items():
        _hits = sum(1 for kw in _cert_keywords if kw in _txt)
        if _hits >= 2:
            _bad_pages.add(_pg)
    print(f"[pdf_structure] cert/ack pages skipped: {sorted(_bad_pages)}", flush=True)

    toc_page = _find_toc_page(lines)

    # Find the first page where a real numbered chapter "1. X" begins'''

if old in s:
    s = s.replace(old, new, 1)
    print("Rule 1 inserted")
else:
    print("Pattern NOT found — showing context")
    import re as _re
    for m in _re.finditer(r"toc_page = _find_toc_page", s):
        start = max(0, m.start() - 100)
        end = min(len(s), m.end() + 100)
        print(s[start:end])
        print("---")

p.write_text(s, encoding="utf-8", newline="\n")
print("saved")
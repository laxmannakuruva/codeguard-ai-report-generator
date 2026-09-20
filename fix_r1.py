from pathlib import Path
p = Path(r"D:\codeguard-ai-stage3\artifacts\codeguard-ai\backend\app\services\report_renderer\pdf_structure.py")
s = p.read_text(encoding="utf-8").lstrip("\ufeff")

# Add page-level cert/ack filter after extracting lines
old = '''    toc_page = find_toc_page(lines) if "find_toc_page" in dir() else None'''
new = '''    # --- Rule 1: cert/ack page filter ---
    _cert_keywords = ("certificate", "certify", "signature of", "signature:",
                      "gratitude", "thank you", "dean of", "vice chancellor",
                      "joining report", "we would like", "i would like",
                      "sincerely", "acknowledgement", "acknowledgment")
    _bad_pages = set()
    from collections import defaultdict as _dd
    _page_text = _dd(str)
    for _l in lines:
        _page_text[_l["page"]] += " " + _l["text"].lower()
    for _pg, _txt in _page_text.items():
        _hits = sum(1 for kw in _cert_keywords if kw in _txt)
        if _hits >= 2:
            _bad_pages.add(_pg)
    print(f"[pdf_structure] cert/ack pages skipped: {sorted(_bad_pages)}", flush=True)

    toc_page = find_toc_page(lines) if "find_toc_page" in dir() else None'''
if old in s:
    s = s.replace(old, new, 1)
    print("Rule 1 added")
else:
    print("Rule 1: pattern NOT found")

# Use _bad_pages in the skip set
s = s.replace(
    '    skip_pages = set(range(1, start_page))\n    if toc_page:\n        skip_pages.add(toc_page)',
    '    skip_pages = set(range(1, start_page)) | _bad_pages\n    if toc_page:\n        skip_pages.add(toc_page)',
    1
)

p.write_text(s, encoding="utf-8", newline="\n")
print("saved")
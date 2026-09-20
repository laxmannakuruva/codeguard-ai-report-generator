from pathlib import Path
p = Path(r"D:\codeguard-ai-stage3\artifacts\codeguard-ai\backend\app\services\report_renderer\pdf_structure.py")
s = p.read_text(encoding="utf-8").lstrip("\ufeff")

old = '''    if start_page is None:
        start_page = (toc_page or 4) + 1'''

new = '''    if start_page is None:
        # No numbered chapters — try unnumbered heading detection
        # Look for bold + larger-than-body short lines
        _first_heading = None
        for l in lines:
            if toc_page and l["page"] <= toc_page:
                continue
            t = l["text"].strip()
            if len(t) > 60 or len(t) < 3:
                continue
            if t.endswith("."):
                continue
            if l["bold"] and l["size"] >= body_size + 0.5:
                _first_heading = l["page"]
                break
        if _first_heading:
            start_page = _first_heading
        else:
            start_page = (toc_page or 4) + 1'''

if old in s:
    s = s.replace(old, new, 1)
    print("unnumbered heading detection added")
else:
    print("pattern NOT found")
    import re as _re
    for m in _re.finditer(r"start_page = \(toc_page or 4\)", s):
        print(s[max(0,m.start()-150):m.end()+50])
        print("---")

p.write_text(s, encoding="utf-8", newline="\n")
print("saved")
from pathlib import Path
p = Path(r"D:\codeguard-ai-stage3\artifacts\codeguard-ai\backend\app\services\report_renderer\pdf_structure.py")
s = p.read_text(encoding="utf-8").lstrip("\ufeff")

# Insert depth-1-only filter before final return
old = '''    output.sort(key=lambda c: (c["page"], c["depth"]))
    output = _dedupe_titles(output)
    return output[:40]'''

new = '''    output.sort(key=lambda c: (c["page"], c["depth"]))
    output = _dedupe_titles(output)

    # If 3+ top-level numbered chapters exist, keep only those
    depth1 = [c for c in output if c.get("depth") == 1]
    if len(depth1) >= 3:
        output = depth1

    return output[:40]'''

if old in s:
    s = s.replace(old, new, 1)
    print("depth-1-only filter added")
else:
    print("pattern NOT found — showing context")
    import re as _re
    for m in _re.finditer(r"_dedupe_titles", s):
        print(s[max(0,m.start()-100):m.end()+100])
        print("---")

p.write_text(s, encoding="utf-8", newline="\n")
print("saved")
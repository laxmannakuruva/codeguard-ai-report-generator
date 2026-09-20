from pathlib import Path
p = Path(r"D:\codeguard-ai-stage3\artifacts\codeguard-ai\backend\app\services\report_renderer\pdf_structure.py")
s = p.read_text(encoding="utf-8").lstrip("\ufeff")

old = '''    # If 3+ top-level numbered chapters exist, keep only those
    depth1 = [c for c in output if c.get("depth") == 1]
    if len(depth1) >= 3:
        output = depth1'''

new = '''    # Only filter if subheadings FAR outnumber chapters (noise signal)
    depth1 = [c for c in output if c.get("depth") == 1]
    depth2 = [c for c in output if c.get("depth") == 2]
    if len(depth1) >= 5 and len(depth2) > len(depth1) * 2:
        output = depth1'''

if old in s:
    s = s.replace(old, new, 1)
    print("filter refined")
else:
    print("pattern NOT found")
    import re as _re
    for m in _re.finditer(r"depth1", s):
        print(s[max(0,m.start()-100):m.end()+150])
        print("---")
        break

p.write_text(s, encoding="utf-8", newline="\n")
print("saved")
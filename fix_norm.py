from pathlib import Path
p = Path(r"D:\codeguard-ai-stage3\artifacts\codeguard-ai\backend\app\services\report_renderer\pdf_structure.py")
s = p.read_text(encoding="utf-8").lstrip("\ufeff")

old = '''        _lt = l["text"].lower().strip().rstrip(":").rstrip(".")
        if _lt in ("appendix", "appendices", "references", "bibliography"):
            seen_appendix = True
            continue'''

new = '''        import re as _re
        _lt = l["text"].lower().strip()
        _lt = _re.sub(r"^\\d+(?:\\.\\d+)*\\.?\\s*", "", _lt).strip()
        _lt = _lt.rstrip(":").rstrip(".").strip()
        if _lt in ("appendix", "appendices", "references", "bibliography"):
            seen_appendix = True
            continue'''

if old in s:
    s = s.replace(old, new, 1)
    print("pdf_structure.py: normalize fixed")
else:
    print("pattern NOT found")

p.write_text(s, encoding="utf-8", newline="\n")
print("saved")
from pathlib import Path

p = Path(r"D:\codeguard-ai-stage3\artifacts\codeguard-ai\backend\app\services\report_renderer\content.py")
s = p.read_text(encoding="utf-8").lstrip("\ufeff")

if "CODE_STRIP" not in s:
    old = "    return re.sub(r\"[ \\\\t]+\", \" \", s).strip()"
    new = '''    # CODE_STRIP: cap length so raw code never floods the report
    if len(s) > 1500:
        s = s[:1500].rsplit(" ", 1)[0] + "..."
    return re.sub(r"[ \\\\t]+", " ", s).strip()'''
    if old in s:
        s = s.replace(old, new, 1)
        print("content.py: length cap added")
    else:
        print("anchor not found")
else:
    print("already has CODE_STRIP")

p.write_text(s, encoding="utf-8", newline="\n")
print("saved")
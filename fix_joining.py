from pathlib import Path
p = Path(r"D:\codeguard-ai-stage3\artifacts\codeguard-ai\backend\app\services\report_renderer\pdf_structure.py")
s = p.read_text(encoding="utf-8").lstrip("\ufeff")

# Add extra reject in the heading filter
old = '''        if tl_check == "joining report":
            continue'''
new = '''        if tl_check == "joining report" or tl_check.endswith("joining report"):
            continue
        # Reject any heading containing 'joining' or 'certificate'
        if "joining" in tl_check or "certificate" in tl_check:
            continue'''
if old in s:
    s = s.replace(old, new, 1)
    print("Bug 1 fix added")
else:
    print("pattern not found — checking alternative")

p.write_text(s, encoding="utf-8", newline="\n")
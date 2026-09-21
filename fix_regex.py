from pathlib import Path
import re

p = Path(r"D:\codeguard-ai-stage3\artifacts\codeguard-ai\backend\app\services\report_renderer\content.py")
s = p.read_text(encoding="utf-8").lstrip("\ufeff")

# Remove the aggressive regex if present
s = re.sub(
    r"s = _re\.sub\(r'\\"\\"\\"[^\n]*?r'\\"\\"\\"', '', s\)\n",
    "",
    s
)
s = re.sub(
    r"s = _re\.sub\(r'\\b\(import\|from\|def\|class\)[^\n]*',\n",
    "",
    s
)

# Find the CODE_STRIP block and replace with a safer version
old_block = re.search(
    r"    # CODE_STRIP:[\s\S]*?(?=\n    return re\.sub)",
    s
)
if old_block:
    new_block = '''    # CODE_STRIP: only cap length, don't strip code (safe)
    if len(s) > 1500:
        s = s[:1500].rsplit(" ", 1)[0] + "..."
'''
    s = s[:old_block.start()] + new_block + s[old_block.end():]
    print("CODE_STRIP replaced with length-only version")
else:
    print("CODE_STRIP block not found — showing _clean body:")
    idx = s.find("def _clean")
    print(s[idx:idx+800])

p.write_text(s, encoding="utf-8", newline="\n")
print("saved")
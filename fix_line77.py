from pathlib import Path

p = Path(r"D:\codeguard-ai-stage3\artifacts\codeguard-ai\backend\app\services\report_renderer\content.py")
lines = p.read_text(encoding="utf-8").splitlines(keepends=True)

fixed = False
out = []
for i, line in enumerate(lines, 1):
    if i == 77 and "+ '.'" in line:
        out.append("        s = s[:1500].rsplit(' ', 1)[0] + '...'\n")
        fixed = True
        print(f"line {i} replaced")
    else:
        out.append(line)

if fixed:
    p.write_text("".join(out), encoding="utf-8", newline="\n")
    print("saved")
else:
    print("line 77 not found — showing 70-80")
    for i, line in enumerate(lines[69:80], 70):
        print(f"{i}: {line.rstrip()}")
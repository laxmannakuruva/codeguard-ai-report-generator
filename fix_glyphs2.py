from pathlib import Path
p = Path(r"D:\codeguard-ai-stage3\artifacts\codeguard-ai\src\pages\home.tsx")
s = p.read_text(encoding="utf-8")

# All broken variants → simple ASCII
fixes = [
    ("â¬¢â¬", " · "),
    ("â¬¢", " · "),
    ("â¬¦", "..."),
    ("â€¦", "..."),
    ("Ã¢â‚¬Â¢", " · "),
    ("Ã¢â‚¬Â¦", "..."),
    ("\u2022", " · "),
    ("\u2026", "..."),
]

count = 0
for bad, good in fixes:
    if bad in s:
        n = s.count(bad)
        s = s.replace(bad, good)
        count += n

# Final sweep: strip any stray high-unicode chars we missed
import re
s = re.sub(r"[\u0080-\u00ff]{1,3}(?=[^\x00-\x7F])", "", s)

p.write_text(s, encoding="utf-8", newline="\n")
print(f"cleaned {count} broken sequences")
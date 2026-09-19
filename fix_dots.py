from pathlib import Path
p = Path(r"D:\codeguard-ai-stage3\artifacts\codeguard-ai\src\pages\home.tsx")
s = p.read_text(encoding="utf-8")

# Replace every mangled variant of the middle dot with a clean ·
replacements = [
    "\u00c3\u0192\u00c6\u2019\u00c3\u00a2\u20ac\u0161\u00c3\u201a\u00c2\u00b7",  # triple mangled
    "\u00c3\u201a\u00c2\u00b7",  # double mangled
    "\u00c2\u00b7",  # single mangled
    "ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â·",  # literal 4-level
    "Ã‚Â·",  # literal 2-level
    "Â·",  # literal 1-level
]
count = 0
for bad in replacements:
    if bad in s:
        n = s.count(bad)
        s = s.replace(bad, "·")
        count += n

p.write_text(s, encoding="utf-8", newline="\n")
print(f"Fixed {count} garbled middle-dots")
from pathlib import Path
p = Path(r"D:\codeguard-ai-stage3\artifacts\codeguard-ai\src\pages\home.tsx")
raw = p.read_bytes()
try:
    s = raw.decode("utf-8")
except UnicodeDecodeError:
    s = raw.decode("cp1252")

# Replace all mangled forms
replacements = [
    # em-dash variants
    ("\u00e2\u20ac\u201d", "-"),
    ("\u00e2\u20ac\u201c", "-"),
    ("â€“", "-"),
    ("â€”", "-"),
    ("â€\"", "-"),
    ("Ã¢â‚¬â€", "-"),
    ("\u00c3\u00a2\u00e2\u201a\u00ac\u00e2\u20ac\u009d", "-"),
    # ✕ variants
    ("âœ•", "x"),
    ("\u00e2\u0153\u2022", "x"),
    ("\u00e2\u0153\u2013", "x"),
    ("Ã¢Å“â€¢", "x"),
    ("\u00c3\u00a2\u0153\u201a\u00e2\u20ac\u00a2", "x"),
    # Generic fallback: any remaining mangled 3-byte sequences
]
count = 0
for bad, good in replacements:
    if bad in s:
        n = s.count(bad)
        s = s.replace(bad, good)
        count += n

# Also replace bare middle-dot mangling
if "\u00c2\u00b7" in s:
    s = s.replace("\u00c2\u00b7", "·")
    count += 1
if "Â·" in s:
    s = s.replace("Â·", "·")
    count += 1

p.write_text(s, encoding="utf-8", newline="\n")
print(f"replaced {count} bad sequences")
from pathlib import Path
import re

p = Path(r"D:\codeguard-ai-stage3\artifacts\codeguard-ai\src\pages\home.tsx")
s = p.read_text(encoding="utf-8")

# ---- 1. Remove tick icons from Save + Upload buttons ----
count_tick = 0
for label in ["Save problem statement", "Upload images"]:
    old = '''            {busy === "problem" ? (
              <LoaderCircle size={13} className="animate-spin" />
            ) : (
              <Check size={13} />
            )}
            ''' + label
    new = '''            {busy === "problem" && (
              <LoaderCircle size={13} className="animate-spin" />
            )}
            ''' + label
    if old in s:
        s = s.replace(old, new, 1)
        count_tick += 1

# Also try for "images"
old_img = '''            {busy === "images" ? (
              <LoaderCircle size={13} className="animate-spin" />
            ) : (
              <Check size={13} />
            )}
            Upload images'''
new_img = '''            {busy === "images" && (
              <LoaderCircle size={13} className="animate-spin" />
            )}
            Upload images'''
if old_img in s:
    s = s.replace(old_img, new_img, 1)
    count_tick += 1

print(f"Ticks removed: {count_tick}")

# ---- 2. Fix garbled text (mojibake) ----
# Replace any sequence of Ã ƒ Æ Â characters and dots with clean ·
s = re.sub(r"[\u00c0-\u00ff\u0152-\u0178\u2018-\u201f\u20ac\u0160\u0161\u017d\u017e]+", "", s)

# Replace remaining middle-dot clusters
s = re.sub(r"\s*[·•]\s*", " · ", s)

p.write_text(s, encoding="utf-8", newline="\n")
print("home.tsx saved")
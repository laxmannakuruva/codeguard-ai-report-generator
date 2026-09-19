from pathlib import Path

p = Path(r"D:\codeguard-ai-stage3\artifacts\codeguard-ai\src\pages\home.tsx")
raw = p.read_bytes()

# Classic mojibake fix: bytes have been UTF-8 encoded multiple times
# Try progressively harder decodings
fixed_text = None

# Attempt 1: read as utf-8, encode latin-1, decode utf-8
try:
    s = raw.decode("utf-8")
    s2 = s.encode("latin-1", errors="strict").decode("utf-8", errors="strict")
    fixed_text = s2
    print("Fix level 1 succeeded")
except (UnicodeDecodeError, UnicodeEncodeError):
    pass

# Attempt 2 (if 1 failed): double pass
if fixed_text is None:
    try:
        s = raw.decode("utf-8")
        s = s.encode("latin-1", errors="ignore").decode("utf-8", errors="ignore")
        s = s.encode("latin-1", errors="ignore").decode("utf-8", errors="ignore")
        fixed_text = s
        print("Fix level 2 succeeded")
    except Exception as e:
        print(f"Fix level 2 failed: {e}")

# Attempt 3 (if 1 and 2 failed): just strip corrupt chars
if fixed_text is None:
    s = raw.decode("utf-8", errors="replace")
    import re
    s = re.sub(r"[\u00c0-\u00ff\u0152-\u0178\u2018-\u201f\u20ac\u0160\u0161\u017d\u017e]+", "", s)
    fixed_text = s
    print("Fix level 3 (strip fallback) used")

if fixed_text:
    p.write_text(fixed_text, encoding="utf-8", newline="\n")
    print("home.tsx saved")

# Now fix the ticks
s = p.read_text(encoding="utf-8")

old1 = '''            {busy === "problem" ? (
              <LoaderCircle size={13} className="animate-spin" />
            ) : (
              <Check size={13} />
            )}
            Save problem statement'''
new1 = '''            {busy === "problem" && (
              <LoaderCircle size={13} className="animate-spin" />
            )}
            Save problem statement'''
if old1 in s:
    s = s.replace(old1, new1, 1)
    print("Save button: tick removed")
else:
    print("Save button: pattern NOT found")

old2 = '''            {busy === "images" ? (
              <LoaderCircle size={13} className="animate-spin" />
            ) : (
              <Check size={13} />
            )}
            Upload images'''
new2 = '''            {busy === "images" && (
              <LoaderCircle size={13} className="animate-spin" />
            )}
            Upload images'''
if old2 in s:
    s = s.replace(old2, new2, 1)
    print("Upload button: tick removed")
else:
    print("Upload button: pattern NOT found")

p.write_text(s, encoding="utf-8", newline="\n")
print("ALL DONE")
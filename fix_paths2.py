from pathlib import Path
p = Path(r"D:\codeguard-ai-stage3\artifacts\codeguard-ai\backend\app\services\report_renderer\pdf_structure.py")
s = p.read_text(encoding="utf-8").lstrip("\ufeff")

# Remove the filter I added to numbered branch
old_filter = '''            # Skip file-path-like titles (e.g. Final/raw/.../video.mp4)
            tl2 = t.lower()
            if any(ext in tl2 for ext in (".mp4", ".py", ".js", ".ts", ".pdf", ".docx", ".zip", ".csv", ".json", ".html", ".css")):
                continue
            if "/" in t and t.count("/") >= 2:
                continue
            if t.count("/") >= 3:
                continue
            # Skip depth > 2 (drop 1.1.1 and deeper)
            if len(parts) > 2:
                continue
            candidates.append({'''
new_filter = '''            if len(parts) > 2:
                continue
            candidates.append({'''
if old_filter in s:
    s = s.replace(old_filter, new_filter, 1)
    print("removed old filter")

# Find the beginning of the for loop and add universal filter
old_loop_start = '''        t = l["text"]
        tl = t.lower().strip()

        if len(t) > 90:
            continue'''

new_loop_start = '''        t = l["text"]
        tl = t.lower().strip()

        # === UNIVERSAL file-path + depth filter ===
        if any(ext in tl for ext in (".mp4", ".py", ".js", ".ts", ".pdf", ".docx", ".zip", ".csv", ".json", ".html", ".css", ".ipynb", ".png", ".jpg", ".mov", ".avi")):
            continue
        if t.count("/") >= 2:
            continue
        if "/refs/" in tl or "/heads/" in tl or "refs/heads" in tl:
            continue
        # === END filter ===

        if len(t) > 90:
            continue'''

if old_loop_start in s:
    s = s.replace(old_loop_start, new_loop_start, 1)
    print("universal filter added")
else:
    print("loop start pattern NOT found")

p.write_text(s, encoding="utf-8", newline="\n")
print("saved")
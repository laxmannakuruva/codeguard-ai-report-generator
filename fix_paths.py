from pathlib import Path
p = Path(r"D:\codeguard-ai-stage3\artifacts\codeguard-ai\backend\app\services\report_renderer\pdf_structure.py")
s = p.read_text(encoding="utf-8").lstrip("\ufeff")

# Add filter before append in numbered branch
old = '''            candidates.append({
                "title": t, "depth": len(parts), "page": l["page"],
            })
            continue'''

new = '''            # Skip file-path-like titles (e.g. Final/raw/.../video.mp4)
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
            candidates.append({
                "title": t, "depth": len(parts), "page": l["page"],
            })
            continue'''
if old in s:
    s = s.replace(old, new, 1)
    print("file-path + depth filters added")
else:
    print("pattern NOT found")

p.write_text(s, encoding="utf-8", newline="\n")
print("saved")
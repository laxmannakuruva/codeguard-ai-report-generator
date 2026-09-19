from pathlib import Path

B = Path(r"D:\codeguard-ai-stage3\artifacts\codeguard-ai\backend")
RR = B / "app" / "services" / "report_renderer"

# 1. upload.py — save uploaded images to disk too
p = B / "app" / "routes" / "upload.py"
s = p.read_text(encoding="utf-8")

old = """        project.project_images.append({
            "filename": filename,
            "data": data,
            "content_type": f.content_type or "image/png",
        })"""
new = """        project.project_images.append({
            "filename": filename,
            "data": data,
            "content_type": f.content_type or "image/png",
        })
        try:
            from pathlib import Path as _P
            disk_dir = _P(project.root) / "_user_uploads"
            disk_dir.mkdir(exist_ok=True, parents=True)
            safe_name = filename.replace("/", "_").replace("\\\\", "_") or "image.png"
            (disk_dir / safe_name).write_bytes(data)
        except Exception:
            pass"""
if old in s:
    s = s.replace(old, new, 1)
    p.write_text(s, encoding="utf-8", newline="\n")
    print("upload.py OK")
else:
    print("upload.py: pattern NOT found")

# 2. images.py — pick up user uploads, allow smaller images
p = RR / "images.py"
s = p.read_text(encoding="utf-8")
s = s.replace(
    'PREFERRED = ("screenshot", "screens", "docs", "doc", "assets", "images", "img", "media")',
    'PREFERRED = ("_user_uploads", "user_uploads", "screenshot", "screens", "docs", "doc", "assets", "images", "img", "media")',
    1)
s = s.replace("MIN_SIDE = 200", "MIN_SIDE = 50", 1)
p.write_text(s, encoding="utf-8", newline="\n")
print("images.py OK")

# 3. gallery.html.j2 — hide the whole page if no images
p = RR / "templates" / "gallery.html.j2"
p.write_text('''{% if images and images|length > 0 %}
<section class="page front" id="anchor-gallery">
  <h1>Project Image Gallery</h1>
  <div class="rule"></div>
  <div class="gallery">
    {% for img in images %}
      <figure class="gallery-item">
        <img src="{{ img.data_uri }}" alt="{{ img.caption }}">
        <figcaption>Figure {{ loop.index }}: {{ img.caption }}</figcaption>
      </figure>
    {% endfor %}
  </div>
</section>
{% endif %}
''', encoding="utf-8", newline="\n")
print("gallery.html.j2 OK")

# 4. report.css — tables don't split, cover lines stack
p = RR / "styles" / "report.css"
b = p.read_bytes()
try:
    s = b.decode("utf-8")
except UnicodeDecodeError:
    s = b.decode("cp1252")

s += '''

/* Tables should not split across pages */
table.data { page-break-inside: avoid !important; break-inside: avoid !important; }
table.data tr { page-break-inside: avoid !important; break-inside: avoid !important; }

/* Cover: force stacked lines */
.cover .student-line { display: block !important; width: 100% !important; clear: both; }
.cover .by { display: block !important; }
'''
p.write_text(s, encoding="utf-8", newline="\n")
print("report.css OK")

print("ALL DONE")
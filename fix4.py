from pathlib import Path

B = Path(r"D:\codeguard-ai-stage3\artifacts\codeguard-ai\backend")
RR = B / "app" / "services" / "report_renderer"

# 1. api.py — accept uploaded images + gallery page anchor
p = RR / "api.py"
s = p.read_text(encoding="utf-8")
if "from .images import select_project_images" in s and "ReportImage" not in s.split("from .images")[1][:80]:
    s = s.replace("from .images import select_project_images",
                  "from .images import select_project_images, ReportImage", 1)

helper = '''

def _uploaded_to_report_images(uploaded):
    import base64
    from pathlib import Path
    out = []
    for img in uploaded or []:
        data = img.get("data") if isinstance(img, dict) else None
        if not data:
            continue
        mime = (img.get("content_type") if isinstance(img, dict) else None) or "image/png"
        uri = f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"
        name = (img.get("filename") if isinstance(img, dict) else None) or "image"
        caption = Path(name).stem.replace("_", " ").replace("-", " ").capitalize()
        out.append(ReportImage(uri, caption, name))
    return out
'''
if "_uploaded_to_report_images" not in s:
    s = s.replace("def _facts_from_context(ctx):",
                  helper.lstrip() + "\n\ndef _facts_from_context(ctx):", 1)

s = s.replace(
    "def generate_report_pdf(project_profile, sections, sample_pdf=None, project_root=None):",
    "def generate_report_pdf(project_profile, sections, sample_pdf=None, project_root=None, uploaded_images=None):",
    1)

s = s.replace(
    "    imgs = select_project_images(project_root)\n    css_v = tokens_to_css_vars(d)",
    "    uploaded_imgs = _uploaded_to_report_images(uploaded_images)\n"
    "    disk_imgs = select_project_images(project_root)\n"
    "    imgs = (uploaded_imgs + disk_imgs)[:8]\n"
    "    css_v = tokens_to_css_vars(d)", 1)

if '("anchor-gallery", "Project Image Gallery"),' not in s:
    s = s.replace(
        '            ("anchor-appendices", "Appendices"),',
        '            ("anchor-gallery", "Project Image Gallery"),\n'
        '            ("anchor-appendices", "Appendices"),', 1)

p.write_text(s, encoding="utf-8", newline="\n")
print("api.py OK")

# 2. report_pdf.py
p = B / "app" / "services" / "report_pdf.py"
s = p.read_text(encoding="utf-8")
s = s.replace(
    "def render_report_pdf(\n    project_profile,\n    sections,\n    sample_pdf=None,\n    project_root=None,\n) -> bytes:\n    return generate_report_pdf(project_profile, sections, sample_pdf, project_root)",
    "def render_report_pdf(\n    project_profile,\n    sections,\n    sample_pdf=None,\n    project_root=None,\n    uploaded_images=None,\n) -> bytes:\n    return generate_report_pdf(project_profile, sections, sample_pdf, project_root, uploaded_images)",
    1)
p.write_text(s, encoding="utf-8", newline="\n")
print("report_pdf.py OK")

# 3. routes/report.py — pass project_images
p = B / "app" / "routes" / "report.py"
s = p.read_text(encoding="utf-8")
s = s.replace(
    "        project.sample_report_bytes,\n        project.root,\n    )",
    "        project.sample_report_bytes,\n        project.root,\n        project.project_images,\n    )", 1)
p.write_text(s, encoding="utf-8", newline="\n")
print("report.py OK")

# 4. base.html.j2 — include gallery
p = RR / "templates" / "base.html.j2"
s = p.read_text(encoding="utf-8")
if "gallery.html.j2" not in s:
    s = s.replace('{% include "back_matter.html.j2" %}',
                  '{% include "back_matter.html.j2" %}\n{% include "gallery.html.j2" %}', 1)
p.write_text(s, encoding="utf-8", newline="\n")
print("base.html.j2 OK")

# 5. gallery.html.j2
(RR / "templates" / "gallery.html.j2").write_text('''<section class="page front" id="anchor-gallery">
  <h1>Project Image Gallery</h1>
  <div class="rule"></div>

  {% if images and images|length > 0 %}
    <div class="gallery">
      {% for img in images %}
        <figure class="gallery-item">
          <img src="{{ img.data_uri }}" alt="{{ img.caption }}">
          <figcaption>Figure {{ loop.index }}: {{ img.caption }}</figcaption>
        </figure>
      {% endfor %}
    </div>
  {% else %}
    <p class="notice">No images were uploaded for this report.</p>
  {% endif %}
</section>
''', encoding="utf-8", newline="\n")
print("gallery.html.j2 OK")

# 6. toc.html.j2
(RR / "templates" / "toc.html.j2").write_text('''<section class="page front" id="anchor-toc">
  <h1>Table of Contents</h1>
  <div class="rule"></div>

  <ul class="toc-list">
    <li>
      <span class="toc-title">Acknowledgement</span>
      <span class="toc-dots"></span>
      <span class="toc-page" data-toc-anchor="anchor-ack">&mdash;</span>
    </li>

    {% for ch in ctx.chapters %}
    <li>
      <span class="toc-title">{{ ch.heading }}</span>
      <span class="toc-dots"></span>
      <span class="toc-page" data-toc-anchor="anchor-chapter-{{ loop.index }}">&mdash;</span>
    </li>
    {% endfor %}

    <li>
      <span class="toc-title">Project Image Gallery</span>
      <span class="toc-dots"></span>
      <span class="toc-page" data-toc-anchor="anchor-gallery">&mdash;</span>
    </li>
    <li>
      <span class="toc-title">Appendices</span>
      <span class="toc-dots"></span>
      <span class="toc-page" data-toc-anchor="anchor-appendices">&mdash;</span>
    </li>
    <li>
      <span class="toc-title">References</span>
      <span class="toc-dots"></span>
      <span class="toc-page" data-toc-anchor="anchor-references">&mdash;</span>
    </li>
  </ul>
</section>
''', encoding="utf-8", newline="\n")
print("toc.html.j2 OK")

# 7. cover.html.j2
(RR / "templates" / "cover.html.j2").write_text('''<section class="page cover">
  <div class="kicker">Internship / Project Report</div>
  <div class="on">A REPORT</div>
  <div class="on">ON</div>

  <h1 class="project-title">{{ ctx.project_name }}</h1>

  <div class="by">By</div>
  <div class="student-line">{{ ctx.student_name or "Student Name" }}</div>
  <div class="student-line">{{ ctx.roll_number or "Roll Number" }}</div>

  <div class="submission">
    Submitted in partial fulfilment of the requirements of the internship programme.
  </div>

  <div class="date">{{ ctx.today or "" }}</div>
</section>
''', encoding="utf-8", newline="\n")
print("cover.html.j2 OK")

# 8. report.css
p = RR / "styles" / "report.css"
b = p.read_bytes()
try:
    s = b.decode("utf-8")
except UnicodeDecodeError:
    s = b.decode("cp1252")

s += '''

/* TOC: dots + page numbers */
.toc-list { list-style: none !important; padding: 0 !important; margin: 12pt 0 0 0 !important; }
.toc-list li { display: flex !important; align-items: baseline; margin: 8pt 0 !important; }
.toc-list .toc-title { font-weight: 600; flex-shrink: 0; }
.toc-list .toc-dots {
  flex: 1;
  border-bottom: 1pt dotted #333;
  margin: 0 6pt;
  transform: translateY(-4pt);
  min-width: 20pt;
}
.toc-list .toc-page { font-weight: 700; flex-shrink: 0; min-width: 2ch; text-align: right; }

/* Cover stacked lines */
.cover .student-line { display: block !important; width: 100%; font-size: 13pt; margin: 4pt 0; font-weight: 600; }
.cover .by { display: block !important; }

/* Gallery */
.gallery { display: block; margin-top: 12pt; }
.gallery-item { display: block; page-break-inside: avoid; margin: 14pt 0; text-align: center; }
.gallery-item img { max-width: 100%; max-height: 320pt; border: 0.75pt solid #333; padding: 4pt; }
.gallery-item figcaption { font-size: 10pt; font-style: italic; margin-top: 6pt; color: #333; }
'''
p.write_text(s, encoding="utf-8", newline="\n")
print("report.css OK")
print("ALL DONE")
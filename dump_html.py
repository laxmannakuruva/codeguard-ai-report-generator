"""Dump the exact HTML that Chromium renders."""

import sys
import zipfile
import tempfile
import pathlib

sys.path.insert(0, r"D:\codeguard-ai-stage3\artifacts\codeguard-ai\backend")

zip_path = r"C:\Users\K LAXMAN\Downloads\codeguard-ai-cloud-fixed.zip"
pdf_path = r"C:\Users\K LAXMAN\Downloads\internship report (2).pdf"
out_html = pathlib.Path(r"D:\codeguard-ai-stage3\debug.html")

tmp = pathlib.Path(tempfile.mkdtemp())
zipfile.ZipFile(zip_path).extractall(tmp)
sample = pathlib.Path(pdf_path).read_bytes()

from app.services.report_renderer.design import extract_design, tokens_to_css_vars
from app.services.report_renderer.content import build_context, Section
from app.services.report_renderer.images import select_project_images
from app.services.report_renderer.template import render_report_html


class P:
    pass


prof = P()
prof.project_name = "CodeGuard AI"
prof.project_type = "Full-stack web application"
prof.languages = ["Python", "TypeScript"]
prof.frameworks = ["FastAPI", "React"]
prof.libraries = []
prof.frontend = ["React"]
prof.backend = ["FastAPI"]
prof.database = []
prof.apis = ["/api/upload"]
prof.modules = ["upload"]
prof.features = ["ZIP upload"]
prof.entry_points = ["main.py"]
prof.tests = []
prof.important_files = []
prof.readme_summary = "Test"
prof.folder_structure = []

sections = [
    {"title": "Abstract", "content": "Test abstract paragraph."},
    {"title": "Introduction", "content": "Test intro paragraph.\n\nSecond paragraph."},
]

d = extract_design(sample)
ctx = build_context(prof, sections)
ctx["logo_uri"] = d.logo_uri

chapters = []
for s in sections:
    paras = [p.strip() for p in s["content"].split("\n\n") if p.strip()]
    chapters.append(Section(title=s["title"], paragraphs=paras))
for i, ch in enumerate(chapters, 1):
    ch.heading = f"{i}. {ch.title}"
ctx["chapters"] = chapters
ctx["acknowledgement"] = Section(title="Acknowledgement", paragraphs=["Test ack."])
ctx["references_section"] = Section(title="References", paragraphs=["Test ref."])

imgs = select_project_images(tmp)
css_path = pathlib.Path(r"D:\codeguard-ai-stage3\artifacts\codeguard-ai\backend\app\services\report_renderer\styles\report.css")
html = render_report_html(tokens_to_css_vars(d), css_path.read_text(encoding="utf-8"), ctx, imgs)

out_html.write_text(html, encoding="utf-8")
print("HTML written to:", out_html)
print("Size:", len(html), "bytes")
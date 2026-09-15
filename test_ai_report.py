import sys, zipfile, tempfile, pathlib, time

sys.path.insert(0, r"D:\codeguard-ai-stage3\artifacts\codeguard-ai\backend")

zip_path = r"C:\Users\K LAXMAN\Downloads\codeguard-ai-cloud-fixed.zip"
pdf_path = r"C:\Users\K LAXMAN\Downloads\internship report (2).pdf"
out = pathlib.Path(r"D:\codeguard-ai-stage3\report-ai.pdf")

tmp = pathlib.Path(tempfile.mkdtemp())
zipfile.ZipFile(zip_path).extractall(tmp)
print("Extracted ZIP:", tmp)

sample = pathlib.Path(pdf_path).read_bytes()
print("Sample PDF:", len(sample), "bytes")

from app.services.report_renderer import generate_report_pdf


class P:
    pass


prof = P()
prof.project_name = "CodeGuard AI"
prof.project_type = "Full-stack web application"
prof.languages = ["Python", "TypeScript"]
prof.frameworks = ["FastAPI", "React", "Vite"]
prof.libraries = ["PyMuPDF", "Playwright", "Jinja2"]
prof.frontend = ["React", "Vite", "TailwindCSS"]
prof.backend = ["FastAPI", "Uvicorn"]
prof.database = ["PostgreSQL"]
prof.apis = ["/api/upload", "/api/project", "/api/report"]
prof.modules = ["upload", "project", "report"]
prof.features = ["ZIP upload", "project analysis", "PDF report generation"]
prof.entry_points = ["main.py", "app.py"]
prof.tests = []
prof.important_files = ["main.py", "requirements.txt", "pnpm-workspace.yaml"]
prof.readme_summary = "CodeGuard AI analyzes uploaded project archives and generates evidence-based reports."
prof.folder_structure = ["backend/app", "backend/app/routes", "backend/app/services", "frontend/src"]

# Pass EMPTY sections — AI writer will fill them.
sections = []

print("Calling generate_report_pdf (this will take ~8 minutes)...")
start = time.time()
pdf_bytes = generate_report_pdf(prof, sections, sample, tmp)
elapsed = time.time() - start
print(f"Done in {elapsed:.1f}s. PDF size: {len(pdf_bytes)} bytes")

out.write_bytes(pdf_bytes)
print("WROTE:", out)

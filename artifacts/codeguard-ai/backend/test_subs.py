from pathlib import Path
from app.services.report_renderer.pdf_structure import extract_structure
from app.services.report_renderer.ai_writer import _specs_from_headings

data = Path(r"C:\Users\K LAXMAN\Downloads\Final_Flood_Prediction_System_Report.pdf").read_bytes()
headings = extract_structure(data)
specs = _specs_from_headings(headings)
print(f"Total specs: {len(specs)}")
for s in specs:
    lvl = s.get("level", 1)
    indent = "    " if lvl == 2 else ""
    print(f"  L{lvl} {indent}{s['title']}")
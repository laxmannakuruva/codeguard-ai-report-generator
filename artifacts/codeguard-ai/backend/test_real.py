from pathlib import Path
from app.services.report_renderer.pdf_structure import extract_structure
from app.services.report_renderer.ai_writer import _specs_from_headings, _roman_fix
from app.services.report_renderer.content import _clean

pdf_path = r"C:\Users\K LAXMAN\Downloads\Final_Flood_Prediction_System_Report.pdf"

print("=" * 60)
print("STEP 1: Extract headings from real sample PDF")
print("=" * 60)
data = Path(pdf_path).read_bytes()
headings = extract_structure(data)
print(f"Raw headings found: {len(headings)}")
for h in headings:
    print(f"  {h['title']}")

print()
print("=" * 60)
print("STEP 2: Filter + auto-prepend (what AI will see)")
print("=" * 60)
specs = _specs_from_headings(headings)
if not specs:
    print("  NONE — would fall back to default chapters")
else:
    print(f"Final chapter list ({len(specs)}):")
    for i, s in enumerate(specs, 1):
        print(f"  {i}. {s['title']}")

print()
print("=" * 60)
print("STEP 3: Roman fix check on simulated output")
print("=" * 60)
sample = "1 express my gratitude. 1 would like to thank everyone."
print(f"  before: {sample}")
print(f"  after:  {_roman_fix(sample)}")

print()
print("=" * 60)
print("STEP 4: HTML entity check")
print("=" * 60)
print(f"  before: PM Kisan &amp;amp; Crop Fertilizer")
print(f"  after:  {_clean('PM Kisan &amp;amp; Crop Fertilizer')}")
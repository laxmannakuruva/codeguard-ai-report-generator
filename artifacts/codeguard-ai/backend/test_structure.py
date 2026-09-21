from pathlib import Path
from app.services.report_renderer.pdf_structure import extract_structure
from app.services.report_renderer.ai_writer import _specs_from_headings
from app.services.report_renderer.content import _clean

# ---- Step 1: extract + filter ----
data = Path(r"C:\Users\K LAXMAN\Downloads\Final_Flood_Prediction_System_Report.pdf").read_bytes()
headings = extract_structure(data)
specs = _specs_from_headings(headings)

# ---- Step 2: simulate AI response (no API call) ----
ai_sections = []
for spec in specs:
    lvl = spec.get("level", 1)
    title = spec["title"]
    content = f"Mock content for {title}. " * 10
    ai_sections.append({"title": title, "content": content, "level": lvl})

# ---- Step 3: rebuild chapters the same way api.py does ----
from app.services.report_renderer.content import Section, Block, _parse_blocks
chapters = []
for item in ai_sections:
    title = item["title"]
    lower = title.lower().strip().rstrip(":").rstrip(".")
    level = item.get("level", 1)
    blocks = _parse_blocks(item["content"])

    # detect ack/abstract/refs
    ack_names = {"acknowledgement", "acknowledgements", "acknowledgment", "acknowledgments"}
    refs_names = {"references", "reference", "bibliography"}
    abs_names = {"abstract", "summary"}
    skip_names = {"appendices", "appendix"}

    # subheading merge
    if level == 2 and chapters:
        parent = chapters[-1]
        parent.blocks.append(Block(type="h2", text=title))
        parent.blocks.extend(blocks)
        continue

    section = Section(title=title, blocks=blocks)
    if lower in ack_names or lower in abs_names or lower in refs_names or lower in skip_names:
        continue
    chapters.append(section)

# ---- Step 4: renumber ----
import re as _re
for i, ch in enumerate(chapters, 1):
    ch.heading = f"{i}. {ch.title}"

# ---- Step 5: print final structure ----
print("=" * 60)
print(f"FINAL REPORT STRUCTURE ({len(chapters)} chapters)")
print("=" * 60)
for ch in chapters:
    print(f"  {ch.heading}")
    for b in ch.blocks:
        if b.type == "h2":
            print(f"      └─ {b.text}")
from pathlib import Path
from app.services.report_renderer.pdf_structure import extract_structure
from app.services.report_renderer.ai_writer import _specs_from_headings
from app.services.report_renderer.content import Section, Block, _parse_blocks, build_context

# ---- Step 1: extract + filter ----
sample = r"C:\Users\K LAXMAN\Downloads\Final_Flood_Prediction_System_Report.pdf"
data = Path(sample).read_bytes()
headings = extract_structure(data)
specs = _specs_from_headings(headings)

# ---- Step 2: build fake chapters ----
chapters = []
for spec in specs:
    lvl = spec.get("level", 1)
    title = spec["title"]
    # Real-looking content
    content = f"This chapter discusses {title.lower()} in detail. " * 6
    blocks = _parse_blocks(content)

    if lvl == 2 and chapters:
        parent = chapters[-1]
        parent.blocks.append(Block(type="h2", text=title))
        parent.blocks.extend(blocks)
        continue

    lower = title.lower().strip().rstrip(":").rstrip(".")
    if lower in {"acknowledgement", "abstract"}:
        continue
    chapters.append(Section(title=title, blocks=blocks))

# renumber
for i, ch in enumerate(chapters, 1):
    ch.heading = f"{i}. {ch.title}"

# ---- Step 3: check for issues ----
issues = []

# Check 3a: duplicate headings
seen = set()
for ch in chapters:
    h = ch.heading.lower()
    if h in seen:
        issues.append(f"DUPLICATE chapter: {ch.heading}")
    seen.add(h)

# Check 3b: empty chapters
for ch in chapters:
    if not ch.blocks:
        issues.append(f"EMPTY chapter: {ch.heading}")

# Check 3c: heading repeated at start of first paragraph
for ch in chapters:
    for b in ch.blocks:
        if b.type == "p" and b.text:
            first_words = b.text[:40].lower()
            heading_start = ch.title.lower()[:20]
            if heading_start in first_words and heading_start:
                issues.append(f"HEADING REPEAT in '{ch.heading}': paragraph starts with '{b.text[:50]}'")
            break

# Check 3d: unreplaced HTML entities
for ch in chapters:
    for b in ch.blocks:
        txt = b.text or ""
        if "&amp;" in txt or "&lt;" in txt or "&gt;" in txt:
            issues.append(f"HTML ENTITY in '{ch.heading}': '{txt[:60]}'")

# Check 3e: chapters with no real words
for ch in chapters:
    word_count = sum(len((b.text or "").split()) for b in ch.blocks if b.type == "p")
    if word_count < 5:
        issues.append(f"TOO SHORT '{ch.heading}': only {word_count} words")

# ---- Step 4: print report ----
print("=" * 60)
print(f"REPORT STRUCTURE: {len(chapters)} chapters")
print("=" * 60)
for ch in chapters:
    print(f"  {ch.heading}")
    for b in ch.blocks:
        if b.type == "h2":
            print(f"      |-- {b.text}")

print()
print("=" * 60)
print(f"ISSUES FOUND: {len(issues)}")
print("=" * 60)
if issues:
    for i in issues:
        print(f"  X {i}")
else:
    print("  All clean — no issues")
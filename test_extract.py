"""TEST ONLY - extracts headings from a PDF by font size. Does not touch production code."""
import sys
from pathlib import Path
import fitz  # PyMuPDF

def extract_structure(pdf_path):
    doc = fitz.open(pdf_path)
    lines = []
    for page_num, page in enumerate(doc, 1):
        d = page.get_text("dict")
        for block in d.get("blocks", []):
            if block.get("type") != 0:
                continue  # skip images
            for line in block.get("lines", []):
                text = "".join(span["text"] for span in line["spans"]).strip()
                if not text:
                    continue
                sizes = [span["size"] for span in line["spans"]]
                bolds = [("bold" in span["font"].lower() or "black" in span["font"].lower())
                         for span in line["spans"]]
                max_size = max(sizes)
                is_bold = any(bolds)
                lines.append({
                    "page": page_num,
                    "text": text,
                    "size": round(max_size, 1),
                    "bold": is_bold,
                })
    doc.close()
    return lines

def guess_headings(lines):
    if not lines:
        return []
    # Body text = most common size
    from collections import Counter
    sizes = [round(l["size"]) for l in lines if len(l["text"]) > 30]
    if not sizes:
        sizes = [round(l["size"]) for l in lines]
    body_size = Counter(sizes).most_common(1)[0][0]

    headings = []
    for l in lines:
        t = l["text"]
        # Skip very long lines
        if len(t) > 120:
            continue
        # Skip lines that end in a period (likely body text)
        if t.endswith(".") and not t.endswith(":"):
            continue
        size_diff = l["size"] - body_size
        # Numbered pattern: "1. Text", "5.1 Text", "5.1.1 Text"
        import re
        numbered = re.match(r"^\d+(\.\d+)*\.?\s+[A-Z]", t)
        # Short + bold OR larger than body
        is_short = len(t) < 80
        looks_heading = numbered or (is_short and (l["bold"] or size_diff >= 1))
        if looks_heading:
            headings.append({
                "page": l["page"],
                "text": t,
                "size": l["size"],
                "bold": l["bold"],
            })
    return headings

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_extract.py <path-to-pdf>")
        sys.exit(1)
    pdf = sys.argv[1]
    if not Path(pdf).exists():
        print(f"File not found: {pdf}")
        sys.exit(1)
    print(f"Analyzing: {pdf}\n")
    lines = extract_structure(pdf)
    headings = guess_headings(lines)

    # Print body size for reference
    from collections import Counter
    sizes = [round(l["size"]) for l in lines if len(l["text"]) > 30]
    if sizes:
        body_size = Counter(sizes).most_common(1)[0][0]
        print(f"Detected body size: {body_size}pt\n")

    print(f"Found {len(headings)} headings:\n")
    print(f"{'PAGE':>4}  {'SIZE':>5}  {'BOLD':>4}  TEXT")
    print("-" * 80)
    for h in headings:
        b = "yes" if h["bold"] else "no"
        print(f"{h['page']:>4}  {h['size']:>5}  {b:>4}  {h['text']}")
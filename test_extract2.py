"""TEST ONLY - improved extractor with filters."""
import sys
import re
from pathlib import Path
import fitz
from collections import Counter

SKIP_KEYWORDS = [
    "a report", "internship completion", "joining report",
    "table of contents", "prepared in partial", "summer internship course",
    "srm university", "by", "on", "at",
]

def extract_lines(pdf_path):
    doc = fitz.open(pdf_path)
    lines = []
    for page_num, page in enumerate(doc, 1):
        d = page.get_text("dict")
        for block in d.get("blocks", []):
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                text = "".join(s["text"] for s in line["spans"]).strip()
                if not text:
                    continue
                sizes = [s["size"] for s in line["spans"]]
                bolds = ["bold" in s["font"].lower() or "black" in s["font"].lower()
                         for s in line["spans"]]
                lines.append({
                    "page": page_num,
                    "text": text,
                    "size": round(max(sizes), 1),
                    "bold": any(bolds),
                })
    doc.close()
    return lines

def filter_headings(lines):
    # Find the page where the numbered chapters begin (skips cover, certs, TOC)
    start_page = None
    for l in lines:
        if re.match(r"^1\.\s+[A-Z]", l["text"]) and l["size"] >= 15:
            start_page = l["page"]
            break
    if start_page is None:
        start_page = 3  # fallback

    headings = []
    for l in lines:
        if l["page"] < start_page:
            continue
        t = l["text"]
        tl = t.lower().strip()

        # Skip keywords
        if any(tl == kw or tl.startswith(kw + " ") for kw in SKIP_KEYWORDS):
            continue

        # Skip TOC entries (end with a page number like "3")
        if re.search(r"\s+\d{1,3}$", t) and not re.match(r"^\d+(\.\d+)*\s", t):
            continue

        # Skip long lines (likely body text)
        if len(t) > 100:
            continue

        # Skip figure captions
        if t.lower().startswith("figure "):
            continue

        # Detect numbered heading: 1. Text / 5.1 Text / 5.1.1 Text
        m = re.match(r"^(\d+(?:\.\d+)*)\.?\s+(.+)$", t)
        if m:
            depth = m.group(1).count(".") + 1  # 1 for chapter, 2 for subheading
            headings.append({
                "page": l["page"],
                "text": t,
                "size": l["size"],
                "bold": l["bold"],
                "depth": depth,
            })
            continue

        # Unnumbered heading (Acknowledgements, Abstract, Brief History)
        # Only count if short, bold, and NOT ending in period
        if len(t) < 60 and l["bold"] and not t.endswith("."):
            # Skip if it's a table cell (short 1-2 word without capital structure)
            headings.append({
                "page": l["page"],
                "text": t,
                "size": l["size"],
                "bold": l["bold"],
                "depth": 2,  # assume subheading if unnumbered
            })

    return headings

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_extract2.py <pdf>")
        sys.exit(1)
    pdf = sys.argv[1]
    lines = extract_lines(pdf)
    headings = filter_headings(lines)

    print(f"Detected {len(headings)} headings:\n")
    for h in headings:
        indent = "  " * (h["depth"] - 1)
        print(f"  P{h['page']:>3}  {indent}{h['text']}")
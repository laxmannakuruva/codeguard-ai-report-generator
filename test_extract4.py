"""TEST v4 - skip cover, certs, TOC. Keep real body chapters."""
import sys
import re
from pathlib import Path
import fitz
from collections import Counter

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

def find_toc_page(lines):
    for l in lines:
        tl = l["text"].lower().strip().rstrip(":")
        if tl in ("table of contents", "contents"):
            return l["page"]
    return None

def detect_structure(lines):
    if not lines:
        return []

    # Body size = most common size among LONG lines
    body_sizes = [round(l["size"]) for l in lines if len(l["text"]) > 60]
    if not body_sizes:
        body_sizes = [round(l["size"]) for l in lines]
    body_size = Counter(body_sizes).most_common(1)[0][0]

    # Find TOC page (skip that whole page)
    toc_page = find_toc_page(lines)

    # Find first real chapter page (numbered 1. with big size)
    start_page = None
    for l in lines:
        if toc_page and l["page"] <= toc_page:
            continue
        if re.match(r"^1\.\s+[A-Z]", l["text"]) and l["size"] >= body_size + 1:
            start_page = l["page"]
            break
    if start_page is None:
        start_page = (toc_page or 2) + 1

    # Candidates
    candidates = []
    for l in lines:
        # Skip cover, certs, TOC
        if l["page"] < start_page:
            continue
        if toc_page and l["page"] == toc_page:
            continue

        t = l["text"]
        tl = t.lower().strip()

        # Basic filters
        if len(t) > 90:
            continue
        if t.endswith(".") and not t.endswith(":"):
            continue
        if tl.startswith(("figure ", "table ")):
            continue
        if re.match(r"^\d+\.\s+[A-Z][a-z]+.*\(\d{4}\)", t):  # reference entry
            continue

        size_diff = l["size"] - body_size

        # Numbered heading: 1. / 5.1 / 5.1.1
        m = re.match(r"^(\d+(?:\.\d+){0,3})\.?\s+(.+)$", t)
        if m:
            num = m.group(1)
            rest = m.group(2)
            if not rest[:1].isupper():
                continue
            parts = [int(p) for p in num.split(".")]
            if any(p > 20 for p in parts):
                continue
            if re.search(r"\s+\d{1,3}$", t):  # ends with page number (TOC leftover)
                continue
            candidates.append({
                "page": l["page"], "text": t, "size": l["size"],
                "depth": len(parts),
            })
            continue

        # Unnumbered heading — bold, larger than body, short
        if l["bold"] and size_diff >= 1 and len(t) < 60:
            # Skip single words (table headers)
            words = t.split()
            if len(words) == 1 and len(t) < 25:
                if tl not in ("acknowledgements", "acknowledgment", "abstract", "references"):
                    continue
            candidates.append({
                "page": l["page"], "text": t, "size": l["size"],
                "depth": 2,
            })

    # Deduplicate — keep FIRST occurrence (real body, not TOC since TOC is skipped)
    seen = set()
    output = []
    for c in candidates:
        key = c["text"].lower().strip().rstrip(":")
        if key in seen:
            continue
        seen.add(key)
        output.append(c)

    output.sort(key=lambda c: (c["page"], c["depth"]))
    return output[:40]

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_extract4.py <pdf>")
        sys.exit(1)
    pdf = sys.argv[1]
    lines = extract_lines(pdf)
    headings = detect_structure(lines)

    print(f"Detected {len(headings)} headings:\n")
    for h in headings:
        indent = "  " * (h["depth"] - 1)
        print(f"  P{h['page']:>3}  {indent}{h['text']}")
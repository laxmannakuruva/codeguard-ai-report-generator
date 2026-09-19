"""TEST v3 - stricter heading extractor."""
import sys
import re
from pathlib import Path
import fitz
from collections import Counter, defaultdict

STOP_SECTIONS = ["references", "bibliography", "appendix", "appendices"]

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

def detect_structure(lines):
    if not lines:
        return []

    # 1. Body size = most common size among LONG lines (> 60 chars)
    body_sizes = [round(l["size"]) for l in lines if len(l["text"]) > 60]
    if not body_sizes:
        body_sizes = [round(l["size"]) for l in lines]
    body_size = Counter(body_sizes).most_common(1)[0][0]

    # 2. Find where references / appendices start (to stop)
    stop_page = None
    for l in lines:
        tl = l["text"].lower().strip().rstrip(":").rstrip(".")
        if tl in STOP_SECTIONS and l["size"] >= body_size:
            stop_page = l["page"]
            break

    # 3. Collect candidates
    candidates = []
    for l in lines:
        if stop_page and l["page"] > stop_page:
            continue
        t = l["text"]
        # Skip too long
        if len(t) > 90:
            continue
        # Skip lines ending in period (body text)
        if t.endswith(".") and not t.endswith(":"):
            continue
        # Skip figure captions
        if t.lower().startswith(("figure ", "table ")):
            continue
        # Skip reference-list entries (start with "N. Name (year)")
        if re.match(r"^\d+\.\s+[A-Z][a-z]+.*\(\d{4}\)", t):
            continue

        size_diff = l["size"] - body_size

        # Numbered pattern only (1. / 5.1 / 5.1.1)
        m = re.match(r"^(\d+(?:\.\d+){0,3})\.?\s+(.+)$", t)
        if m:
            num = m.group(1)
            rest = m.group(2)
            # Must start with capital
            if not rest[:1].isupper():
                continue
            # Numbers should be small (not "196 countries", "2021")
            parts = [int(p) for p in num.split(".")]
            if any(p > 20 for p in parts):
                continue
            # Skip TOC-like lines ("5. Text 5" — ends with page number)
            if re.search(r"\s+\d{1,3}$", t) and not re.match(r"^\d+(\.\d+)*\s", t):
                continue
            depth = len(parts)
            candidates.append({
                "page": l["page"], "text": t, "size": l["size"],
                "bold": l["bold"], "depth": depth, "kind": "numbered",
            })
            continue

        # Unnumbered heading — must be BOLD and either top-2 size tier OR very short
        if l["bold"] and size_diff >= 0.5 and len(t) < 50:
            # Skip single-word table headers (Category, Tier, Purpose)
            words = t.split()
            if len(words) == 1 and len(t) < 20:
                # Allow "Acknowledgements", "Abstract", "References"
                if t.lower() not in ("acknowledgements", "acknowledgment", "abstract", "references"):
                    continue
            # Skip if it contains "&amp" or table junk
            if "&amp" in t.lower() or "&" in t and "scheme" in t.lower():
                continue
            candidates.append({
                "page": l["page"], "text": t, "size": l["size"],
                "bold": l["bold"], "depth": 2, "kind": "unnumbered",
            })

    # 4. Deduplicate (TOC on page 5 duplicates chapter titles)
    seen = set()
    output = []
    for c in candidates:
        key = c["text"].lower().strip()
        if key in seen:
            continue
        seen.add(key)
        output.append(c)

    # 5. Sort by page, then depth
    output.sort(key=lambda c: (c["page"], c["depth"]))

    # 6. Keep only the first 35 to limit noise
    return output[:35]

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_extract3.py <pdf>")
        sys.exit(1)
    pdf = sys.argv[1]
    lines = extract_lines(pdf)
    headings = detect_structure(lines)

    print(f"Detected {len(headings)} headings:\n")
    for h in headings:
        indent = "  " * (h["depth"] - 1)
        print(f"  P{h['page']:>3}  {indent}{h['text']}")
"""Extract headings structure from a PDF (sample report)."""
import re
import sys
from collections import Counter
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None


def _extract_lines(pdf_bytes):
    if fitz is None:
        return []
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
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
                    "page": page_num, "text": text,
                    "size": round(max(sizes), 1), "bold": any(bolds),
                })
    doc.close()
    return lines


def _find_toc_page(lines):
    for l in lines:
        tl = l["text"].lower().strip().rstrip(":")
        if tl in ("table of contents", "contents"):
            return l["page"]
    return None


def extract_structure(pdf_bytes):
    """Return list of {title, depth, page} from a sample PDF. Empty list on failure."""
    try:
        lines = _extract_lines(pdf_bytes)
    except Exception:
        return []
    if not lines:
        return []

    body_sizes = [round(l["size"]) for l in lines if len(l["text"]) > 60]
    if not body_sizes:
        body_sizes = [round(l["size"]) for l in lines]
    if not body_sizes:
        return []
    body_size = Counter(body_sizes).most_common(1)[0][0]

    toc_page = _find_toc_page(lines)

    start_page = None
    for l in lines:
        if toc_page and l["page"] <= toc_page:
            continue
        if re.match(r"^1\.\s+[A-Z]", l["text"]) and l["size"] >= body_size + 1:
            start_page = l["page"]
            break
    if start_page is None:
        start_page = (toc_page or 2) + 1

    stop_page = None
    for l in lines:
        tl = l["text"].lower().strip().rstrip(":").rstrip(".")
        if tl in ("references", "bibliography") and l["page"] >= start_page:
            stop_page = l["page"]
            break

    candidates = []
    max_chapter = 0

    for l in lines:
        if l["page"] < start_page:
            continue
        if toc_page and l["page"] == toc_page:
            continue
        if stop_page and l["page"] >= stop_page:
            continue

        t = l["text"]
        tl = t.lower().strip()

        if len(t) > 90:
            continue
        if t.endswith(".") and not t.endswith(":"):
            continue
        if tl.startswith(("figure ", "table ")):
            continue
        if re.match(r"^\d+\.\s+[A-Z][a-z]+.*\(\d{4}\)", t):
            continue

        size_diff = l["size"] - body_size

        m = re.match(r"^(\d+(?:\.\d+){0,3})\.?\s+(.+)$", t)
        if m:
            num = m.group(1)
            rest = m.group(2)
            if not rest[:1].isupper():
                continue
            parts = [int(p) for p in num.split(".")]
            if any(p > 20 for p in parts):
                continue
            if re.search(r"\s+\d{1,3}$", t):
                continue

            top = parts[0]
            if len(parts) == 1:
                if top <= max_chapter and max_chapter > 3:
                    continue
                max_chapter = max(max_chapter, top)

            candidates.append({
                "title": t, "depth": len(parts), "page": l["page"],
            })
            continue

        if l["bold"] and size_diff >= 1 and len(t) < 60:
            words = t.split()
            if len(words) == 1 and len(t) < 25:
                if tl not in ("acknowledgements", "acknowledgment", "abstract", "references"):
                    continue
            candidates.append({
                "title": t, "depth": 2, "page": l["page"],
            })

    seen = set()
    output = []
    for c in candidates:
        key = c["title"].lower().strip().rstrip(":")
        if key in seen:
            continue
        seen.add(key)
        output.append(c)

    output.sort(key=lambda c: (c["page"], c["depth"]))
    return output[:40]


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python pdf_structure.py <pdf>")
        sys.exit(1)
    data = Path(sys.argv[1]).read_bytes()
    result = extract_structure(data)
    print(f"Found {len(result)} headings:\n")
    for h in result:
        indent = "  " * (h["depth"] - 1)
        print(f"  {indent}{h['title']}")
"""Page-by-page QA on the final PDF bytes."""

import logging
from dataclasses import dataclass

import fitz

log = logging.getLogger(__name__)
MIN_INK = 0.004
MAX_EDGE = 0.03
EDGE = 8


@dataclass
class PageQAResult:
    index: int
    ink_ratio: float
    edge_ink_ratio: float
    verdict: str


def inspect_pdf_bytes(pdf_bytes, dpi=72):
    out = []
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as e:
        log.warning("QA open failed: %s", e)
        return out
    try:
        for i, page in enumerate(doc):
            pix = page.get_pixmap(dpi=dpi, colorspace=fitz.csRGB)
            s = pix.samples
            w, h = pix.width, pix.height
            total = w * h
            if not total:
                continue
            nw = ew = 0
            for y in range(h):
                row = y * w * 3
                near_y = y < EDGE or y >= h - EDGE
                for x in range(w):
                    o = row + x * 3
                    if s[o] < 245 or s[o + 1] < 245 or s[o + 2] < 245:
                        nw += 1
                        if near_y or x < EDGE or x >= w - EDGE:
                            ew += 1
            ink = nw / total
            edge = ew / total
            v = "ok"
            if ink < MIN_INK:
                v = "mostly_blank"
            elif edge > MAX_EDGE:
                v = "possible_clip"
            out.append(PageQAResult(i, round(ink, 4), round(edge, 4), v))
    finally:
        doc.close()
    return out


def format_qa_report(results):
    if not results:
        return "QA: no pages."
    lines = ["QA report", "-" * 40]
    for r in results:
        lines.append(
            f"page {r.index + 1:>3}  ink={r.ink_ratio:.4f}  "
            f"edge={r.edge_ink_ratio:.4f}  {r.verdict}"
        )
    bad = [r for r in results if r.verdict != "ok"]
    lines.append("-" * 40)
    lines.append(f"pages={len(results)}  issues={len(bad)}")
    if bad:
        lines.append("flagged: " + ", ".join(str(r.index + 1) for r in bad))
    return "\n".join(lines)
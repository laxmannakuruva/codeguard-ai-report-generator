"""Extract design tokens from the sample PDF."""

import base64
import re
from dataclasses import dataclass, field

import fitz
from .exceptions import DesignExtractionError
CONFLICT_RE = re.compile(
    r"<<<<<<<.*?(?:\n|$)|=======.*?(?:\n|$)|>>>>>>>.*?(?:\n|$)", re.S
)
NUMBER_RE = re.compile(r"^\s*(\d+(?:\.\d+)*)[.)]?\s+(.+?)\s*$")


@dataclass
class OutlineItem:
    number: str
    title: str
    level: int


@dataclass
class DesignTokens:
    width_pt: float = 595.0
    height_pt: float = 842.0
    margin_top_pt: float = 72.0
    margin_bottom_pt: float = 72.0
    margin_left_pt: float = 72.0
    margin_right_pt: float = 72.0
    serif_family: str = "'Times New Roman', Georgia, serif"
    sans_family: str = "'Helvetica Neue', Arial, sans-serif"
    body_size_pt: float = 11.0
    heading_size_pt: float = 16.0
    subheading_size_pt: float = 12.5
    caption_size_pt: float = 9.5
    ink: str = "#111111"
    accent: str = "#1f3a5f"
    rule: str = "#333333"
    border: str = "#222222"
    has_page_border: bool = False
    border_inset_pt: float = 24.0
    border_width_pt: float = 0.8
    logo_uri: str = None
    outline: list = field(default_factory=list)
    observed_fonts: list = field(default_factory=list)


def _clean(t):
    return CONFLICT_RE.sub("", t or "").strip()


def _to_hex(rgb):
    return "#%02x%02x%02x" % rgb


def _outline(doc):
    items = []
    for page in doc:
        for raw in page.get_text("text").splitlines():
            m = NUMBER_RE.match(_clean(raw))
            if m:
                num, title = m.groups()
                if len(title) <= 100:
                    items.append(OutlineItem(num, title, len(num.split("."))))
    seen = set()
    out = []
    for i in items:
        k = f"{i.number}:{i.title.lower()}"
        if k not in seen:
            seen.add(k)
            out.append(i)
    return out


def _repeated_logo(doc):
    counts = {}
    for page in doc:
        for img in page.get_images(full=True):
            counts[img[0]] = counts.get(img[0], 0) + 1
    rep = [x for x, n in counts.items() if n >= 3]
    if not rep:
        return None
    try:
        ext = doc.extract_image(rep[0])
        data = ext.get("image")
        if not data:
            return None
        e = ext.get("ext", "png").lower()
        mime = "image/jpeg" if e in ("jpg", "jpeg") else f"image/{e}"
        return f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"
    except Exception:
        return None


def extract_design(sample_pdf):
    if not sample_pdf:
        raise DesignExtractionError("empty sample pdf")
    doc = fitz.open(stream=sample_pdf, filetype="pdf")
    try:
        t = DesignTokens()
        first = doc[0]
        w, h = float(first.rect.width), float(first.rect.height)
        if first.rotation in (90, 270):
            w, h = h, w
        t.width_pt, t.height_pt = w, h

        sizes, fonts, colors, xs, ys = [], [], [], [], []
        for page in doc:
            for b in page.get_text("dict").get("blocks", []):
                for line in b.get("lines", []):
                    for s in line.get("spans", []):
                        if s.get("size"):
                            sizes.append(float(s["size"]))
                        if s.get("font"):
                            fonts.append(str(s["font"]))
                        c = s.get("color")
                        if isinstance(c, int):
                            colors.append(((c >> 16) & 255, (c >> 8) & 255, c & 255))
                        bb = s.get("bbox")
                        if bb:
                            xs.append(float(bb[0]))
                            ys.append(float(bb[1]))

        if sizes:
            ss = sorted(sizes)
            med = ss[len(ss) // 2]
            t.body_size_pt = max(9.5, min(12.5, med))
            t.heading_size_pt = max(t.body_size_pt + 3, min(24.0, ss[int(len(ss) * 0.95) - 1]))
            t.subheading_size_pt = max(t.body_size_pt + 1.2, t.heading_size_pt - 1.5)
            t.caption_size_pt = max(8.0, t.body_size_pt - 1.2)

        if fonts:
            t.observed_fonts = sorted(set(fonts))[:12]
            if any("times" in f.lower() or "georgia" in f.lower() for f in fonts):
                t.serif_family = "'Times New Roman', Georgia, serif"

        if colors:
            dark = [c for c in colors if max(c) < 90]
            if dark:
                t.ink = _to_hex(max(set(dark), key=dark.count))
            sat = [c for c in colors if max(c) >= 40 and min(c) <= 235 and max(c) - min(c) >= 20]
            if sat:
                t.accent = _to_hex(max(set(sat), key=sat.count))
                t.rule = t.accent

        t.margin_left_pt = max(42.0, min(min(xs) if xs else 72.0, w * 0.18))
        t.margin_right_pt = max(42.0, min(w - max(xs) if xs else 72.0, w * 0.18))
        t.margin_top_pt = max(42.0, min(min(ys) if ys else 72.0, h * 0.16))
        t.margin_bottom_pt = max(42.0, min(h - max(ys) if ys else 72.0, h * 0.16))

        t.logo_uri = _repeated_logo(doc)
        t.outline = _outline(doc)
        return t
    finally:
        doc.close()


def tokens_to_css_vars(t):
    return "\n".join([
        ":root {",
        f"  --page-w: {t.width_pt}pt;",
        f"  --page-h: {t.height_pt}pt;",
        f"  --m-top: {t.margin_top_pt}pt;",
        f"  --m-bottom: {t.margin_bottom_pt}pt;",
        f"  --m-left: {t.margin_left_pt}pt;",
        f"  --m-right: {t.margin_right_pt}pt;",
        f"  --font-serif: {t.serif_family};",
        f"  --font-sans: {t.sans_family};",
        f"  --size-body: {t.body_size_pt}pt;",
        f"  --size-h1: {t.heading_size_pt}pt;",
        f"  --size-h2: {t.subheading_size_pt}pt;",
        f"  --size-cap: {t.caption_size_pt}pt;",
        f"  --ink: {t.ink};",
        f"  --accent: {t.accent};",
        f"  --rule: {t.rule};",
        f"  --border: {t.border};",
        f"  --border-inset: {t.border_inset_pt}pt;",
        f"  --border-width: {t.border_width_pt}pt;",
        "}",
    ])
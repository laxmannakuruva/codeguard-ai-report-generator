"""Report generation entry point (WeasyPrint)."""

import logging
import re
from pathlib import Path

from .design import extract_design, tokens_to_css_vars
from .content import build_context, Section, _parse_blocks
from .images import select_project_images, ReportImage
from .template import render_report_html
from .exceptions import ReportRenderError

log = logging.getLogger(__name__)
TOC_RE = re.compile(r'data-toc-anchor="([^"]+)"')


def _css_body():
    return (Path(__file__).parent / "styles" / "report.css").read_text(encoding="utf-8")


def _inject(html, pages):
    def repl(m):
        a = m.group(1)
        n = pages.get(a)
        return f'<span class="toc-page" data-toc-anchor="{a}">{n if n else "—"}</span>'
    return re.sub(
        r'<span class="toc-page" data-toc-anchor="([^"]+)">[^<]*</span>',
        repl, html,
    )


def _render_pdf(html: str) -> bytes:
    from weasyprint import HTML
    return HTML(string=html).write_pdf()


def _measure_pages_from_pdf(pdf_bytes, chapters):
    """Search rendered PDF for chapter headings. Skip first 4 pages (cover, ack, toc)."""
    import fitz

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    total = len(doc)
    SKIP = 4
    result = {}
    try:
        for i, ch in enumerate(chapters, 1):
            found = None
            for pn in range(SKIP, total):
                if doc[pn].search_for(ch.heading):
                    found = pn + 1
                    break
            result[f"anchor-chapter-{i}"] = found or (SKIP + i)

        for anchor, text in [
            ("anchor-ack", "Acknowledgement"),
            ("anchor-gallery", "Project Image Gallery"),
            ("anchor-appendices", "Appendices"),
            ("anchor-references", "References"),
        ]:
            found = None
            for pn in range(1, total):
                if doc[pn].search_for(text):
                    found = pn + 1
                    break
            result[anchor] = found or 1
    finally:
        doc.close()
    return result


def _uploaded_to_report_images(uploaded):
    import base64
    from pathlib import Path
    out = []
    for img in uploaded or []:
        data = img.get("data") if isinstance(img, dict) else None
        if not data:
            continue
        mime = (img.get("content_type") if isinstance(img, dict) else None) or "image/png"
        uri = f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"
        name = (img.get("filename") if isinstance(img, dict) else None) or "image"
        caption = Path(name).stem.replace("_", " ").replace("-", " ").capitalize()
        out.append(ReportImage(uri, caption, name))
    return out


def _facts_from_context(ctx):
    return {k: ctx.get(k, "" if not isinstance(ctx.get(k), list) else []) for k in [
        "project_name", "project_type", "languages", "frameworks", "libraries",
        "frontend", "backend", "database", "apis", "modules", "features",
        "entry_points", "tests", "important_files", "folder_structure", "readme_summary",
    ]}


def _ai_to_chapters(ai_sections):
    chapters, ack, refs = [], None, None
    for item in ai_sections:
        title = (item.get("title") or "").strip()
        lower = title.lower()
        content = item.get("content", "")
        blocks = _parse_blocks(content)
        paragraphs = [b.text for b in blocks if b.type == "p"]
        section = Section(title=title, paragraphs=paragraphs, blocks=blocks)
        if lower == "acknowledgement":
            ack = section
        elif lower == "references":
            refs = section
        else:
            chapters.append(section)
    for i, ch in enumerate(chapters, 1):
        ch.heading = f"{i}. {ch.title}"
    return chapters, ack, refs


def generate_report_pdf(project_profile, sections, sample_pdf=None, project_root=None, uploaded_images=None):
    if not sample_pdf:
        raise ReportRenderError("A sample PDF is required.")

    d = extract_design(sample_pdf)
    ctx = build_context(project_profile, sections)
    ctx["logo_uri"] = d.logo_uri

    chapters, ack, refs = [], None, None
    try:
        from . import ai_writer
        print("[AI] Generating sections...", flush=True)
        ai_sections = ai_writer.generate_sections(
            _facts_from_context(ctx),
            progress=lambda m: print(m, flush=True),
        )
        chapters, ack, refs = _ai_to_chapters(ai_sections)
        ctx["chapters"] = chapters
        ctx["acknowledgement"] = ack
        ctx["references_section"] = refs
        print(f"[AI] {len(chapters)} chapters | ack={bool(ack)} | refs={bool(refs)}", flush=True)
    except Exception as exc:
        log.warning("AI generation failed: %s", exc)
        print(f"[AI] FAILED: {exc}", flush=True)

    uploaded_imgs = _uploaded_to_report_images(uploaded_images)
    disk_imgs = select_project_images(project_root)
    imgs = (uploaded_imgs + disk_imgs)[:8]
    css_v = tokens_to_css_vars(d)
    css_b = _css_body()

    html_pass1 = render_report_html(css_v, css_b, ctx, imgs)
    pdf_pass1 = _render_pdf(html_pass1)

    page_numbers = {}
    try:
        page_numbers = _measure_pages_from_pdf(pdf_pass1, chapters)
        print(f"[TOC] page numbers: {page_numbers}", flush=True)
    except Exception as e:
        log.warning("PDF measurement failed: %s", e)

    html_pass2 = _inject(html_pass1, page_numbers)
    return _render_pdf(html_pass2)
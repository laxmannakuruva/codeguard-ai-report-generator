"""Report generation entry point."""

import logging
import re
from pathlib import Path

from playwright.sync_api import sync_playwright

from .design import extract_design, tokens_to_css_vars
from .content import build_context, Section, _parse_blocks
from .images import select_project_images
from .template import render_report_html
from .qa import inspect_pdf_bytes, format_qa_report
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


def _render_once(html, width_pt, height_pt):
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True)
        try:
            p = b.new_page(viewport={"width": round(width_pt), "height": round(height_pt)})
            p.set_content(html, wait_until="load")
            p.wait_for_timeout(250)
            return p.pdf(
                print_background=True,
                prefer_css_page_size=True,
                display_header_footer=False,
                margin={"top": "20mm", "right": "18mm", "bottom": "20mm", "left": "0"},
            )
        finally:
            b.close()


def _measure_pages_from_pdf(pdf_bytes, chapters, has_ack, has_refs):
    """Search rendered PDF for chapter headings. Skip the first 4 pages
    (cover + acknowledgement + TOC) so we don't match TOC entries."""
    import fitz

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    total = len(doc)
    SKIP = 4  # cover (1) + ack (1) + toc (1) + safety (1)
    result = {}
    try:
        for i, ch in enumerate(chapters, 1):
            heading = ch.heading
            found = None
            for pn in range(SKIP, total):
                if doc[pn].search_for(heading):
                    found = pn + 1
                    break
            result[f"anchor-chapter-{i}"] = found or (SKIP + i)

        for anchor, text in [
            ("anchor-ack", "Acknowledgement"),
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


def _facts_from_context(ctx):
    return {
        "project_name": ctx.get("project_name", ""),
        "project_type": ctx.get("project_type", ""),
        "languages": ctx.get("languages", []),
        "frameworks": ctx.get("frameworks", []),
        "libraries": ctx.get("libraries", []),
        "frontend": ctx.get("frontend", []),
        "backend": ctx.get("backend", []),
        "database": ctx.get("database", []),
        "apis": ctx.get("apis", []),
        "modules": ctx.get("modules", []),
        "features": ctx.get("features", []),
        "entry_points": ctx.get("entry_points", []),
        "tests": ctx.get("tests", []),
        "important_files": ctx.get("important_files", []),
        "folder_structure": ctx.get("folder_structure", []),
        "readme_summary": ctx.get("readme_summary", ""),
    }


def _ai_to_chapters(ai_sections):
    chapters = []
    ack = None
    refs = None
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


def generate_report_pdf(project_profile, sections, sample_pdf=None, project_root=None):
    if not sample_pdf:
        raise ReportRenderError("A sample PDF is required.")

    d = extract_design(sample_pdf)
    ctx = build_context(project_profile, sections)
    ctx["logo_uri"] = d.logo_uri

    facts = _facts_from_context(ctx)
    chapters, ack, refs = [], None, None
    try:
        from . import ai_writer
        print("[AI] Generating sections...", flush=True)
        ai_sections = ai_writer.generate_sections(facts, progress=lambda m: print(m, flush=True))
        chapters, ack, refs = _ai_to_chapters(ai_sections)
        ctx["chapters"] = chapters
        ctx["acknowledgement"] = ack
        ctx["references_section"] = refs
        print(f"[AI] {len(chapters)} chapters | ack={bool(ack)} | refs={bool(refs)}", flush=True)
    except Exception as exc:
        log.warning("AI generation failed: %s", exc)
        print(f"[AI] FAILED: {exc}", flush=True)

    imgs = select_project_images(project_root)
    css_v = tokens_to_css_vars(d)
    css_b = _css_body()

    # PASS 1: render with placeholder TOC numbers
    html_pass1 = render_report_html(css_v, css_b, ctx, imgs)
    pdf_pass1 = _render_once(html_pass1, d.width_pt, d.height_pt)

    # Measure real page numbers from the rendered PDF
    page_numbers = {}
    try:
        page_numbers = _measure_pages_from_pdf(pdf_pass1, chapters, bool(ack), bool(refs))
        print(f"[TOC] measured {len(page_numbers)} anchors", flush=True)
        print(f"[TOC] page numbers: {page_numbers}", flush=True)
    except Exception as e:
        log.warning("PDF measurement failed: %s", e)

    # PASS 2: inject real page numbers, render final PDF
    html_pass2 = _inject(html_pass1, page_numbers)
    pdf_final = _render_once(html_pass2, d.width_pt, d.height_pt)

    try:
        log.info("\n%s", format_qa_report(inspect_pdf_bytes(pdf_final)))
    except Exception as e:
        log.warning("QA failed: %s", e)

    return pdf_final
"""Report generation entry point (AI-powered, ordered correctly)."""

import logging
import re
from pathlib import Path

from playwright.sync_api import sync_playwright

from .design import extract_design, tokens_to_css_vars
from .content import build_context, Section
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


def _measure(html, anchors, ph, mt, mb):
    """Return {anchor_id: page_number}. Cover is page 1."""
    usable = max(1.0, ph - mt - mb)
    res = {}
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True)
        try:
            p = b.new_page()
            p.set_content(html, wait_until="load")
            p.wait_for_timeout(200)
            pos = p.evaluate(
                """(ids) => {
                    const o = {};
                    for (const id of ids) {
                        const el = document.getElementById(id);
                        if (!el) { o[id] = null; continue; }
                        const r = el.getBoundingClientRect();
                        o[id] = r.top + window.scrollY;
                    }
                    return o;
                }""", anchors,
            )
            for a, y in pos.items():
                if y is None:
                    continue
                res[a] = int(y // usable) + 1
        finally:
            b.close()
    return res


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


def _split_paragraphs(text):
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


def _ai_to_chapters(ai_sections):
    """Return (numbered_chapters, acknowledgement, references)."""
    chapters = []
    ack = None
    refs = None
    for item in ai_sections:
        title = (item.get("title") or "").strip()
        lower = title.lower()
        paras = _split_paragraphs(item.get("content", ""))
        if lower == "acknowledgement":
            ack = Section(title=title, paragraphs=paras)
        elif lower == "references":
            refs = Section(title=title, paragraphs=paras)
        else:
            chapters.append(Section(title=title, paragraphs=paras))
    for i, ch in enumerate(chapters, 1):
        ch.heading = f"{i}. {ch.title}"
    return chapters, ack, refs


def generate_report_pdf(project_profile, sections, sample_pdf=None, project_root=None):
    if not sample_pdf:
        raise ReportRenderError("A sample PDF is required.")

    d = extract_design(sample_pdf)
    ctx = build_context(project_profile, sections)
    ctx["logo_uri"] = d.logo_uri

    # -------- 1. AI generation --------
    facts = _facts_from_context(ctx)
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

    # -------- 2. Images --------
    imgs = select_project_images(project_root)

    # -------- 3. Render HTML --------
    css_v = tokens_to_css_vars(d)
    css_b = _css_body()
    h1 = render_report_html(css_v, css_b, ctx, imgs)

    # -------- 4. Two-pass TOC page numbers --------
    anchors = TOC_RE.findall(h1)
    pages = {}
    if anchors:
        try:
            pages = _measure(h1, anchors, d.height_pt, d.margin_top_pt, d.margin_bottom_pt)
            print(f"[TOC] measured {len(pages)} anchors", flush=True)
        except Exception as e:
            log.warning("anchor measure failed: %s", e)

    hf = _inject(h1, pages)

    # -------- 5. PDF --------
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True)
        try:
            p = b.new_page(
                viewport={"width": round(d.width_pt), "height": round(d.height_pt)},
                device_scale_factor=1,
            )
            p.set_content(hf, wait_until="load")
            p.wait_for_timeout(250)
            pdf = p.pdf(
                print_background=True,
                prefer_css_page_size=True,
                display_header_footer=False,
                margin={"top": "22mm", "right": "22mm", "bottom": "22mm", "left": "22mm"},
            )
        finally:
            b.close()

    try:
        log.info("\n%s", format_qa_report(inspect_pdf_bytes(pdf)))
    except Exception as e:
        log.warning("QA failed: %s", e)

    return pdf
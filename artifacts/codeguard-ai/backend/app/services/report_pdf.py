"""Thin adapter for report_pdf."""

from .report_renderer import generate_report_pdf


def render_report_pdf(
    project_profile,
    sections,
    sample_pdf=None,
    project_root=None,
    uploaded_images=None,
) -> bytes:
    return generate_report_pdf(project_profile, sections, sample_pdf, project_root, uploaded_images)
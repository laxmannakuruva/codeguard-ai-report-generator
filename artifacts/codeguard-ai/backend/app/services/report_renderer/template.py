"""Jinja2 environment for report templates."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

TEMPLATES_DIR = Path(__file__).parent / "templates"


def build_environment():
    return Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=False,
    )


def render_report_html(css_vars, css_body, context, images):
    env = build_environment()
    return env.get_template("base.html.j2").render(
        css_vars=css_vars,
        css_body=css_body,
        ctx=context,
        images=images,
    )
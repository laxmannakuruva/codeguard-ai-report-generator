from pathlib import Path

p = Path(r"D:\codeguard-ai-stage3\artifacts\codeguard-ai\backend\app\services\report_renderer\ai_writer.py")
s = p.read_text(encoding="utf-8")

# 1. Change generate_sections signature to accept custom_headings
old_sig = "def generate_sections(facts, progress=None):"
new_sig = "def generate_sections(facts, progress=None, custom_headings=None):"
if old_sig in s:
    s = s.replace(old_sig, new_sig, 1)
    print("ai_writer.py: signature updated")
else:
    print("ai_writer.py: signature pattern NOT found")

# 2. Add logic to build spec list from custom_headings
old_body = '''def generate_sections(facts, progress=None, custom_headings=None):
    out = []
    for i, spec in enumerate(SECTION_SPECS, start=1):'''
new_body = '''def _specs_from_headings(headings):
    """Build SECTION_SPECS-like list from extracted headings."""
    if not headings or len(headings) < 5:
        return None
    out = []
    for h in headings:
        title = (h.get("title") or "").strip()
        # Strip leading number: "5.1 Objectives" -> "Objectives"
        import re as _re
        clean = _re.sub(r"^\\d+(?:\\.\\d+)*\\.?\\s*", "", title).strip()
        if not clean:
            clean = title
        out.append({
            "title": clean,
            "focus_keys": ["project_name", "project_type", "readme_summary",
                           "languages", "frameworks", "libraries",
                           "frontend", "backend", "database",
                           "apis", "modules", "features",
                           "entry_points", "tests", "important_files"],
            "instruction": (
                f"Write a detailed section titled '{clean}'. "
                "Base it only on the project facts provided. "
                "Use 2-4 short paragraphs. If helpful, include one "
                "markdown table (| Column | Column |) or a [FIGURE: caption] "
                "line. Do not repeat the heading at the start of the paragraph."
            ),
        })
    return out


def generate_sections(facts, progress=None, custom_headings=None):
    specs_to_use = _specs_from_headings(custom_headings) if custom_headings else None
    if not specs_to_use:
        specs_to_use = SECTION_SPECS
        print("[AI] Using default SECTION_SPECS", flush=True)
    else:
        print(f"[AI] Using {len(specs_to_use)} custom headings from sample PDF", flush=True)
    out = []
    for i, spec in enumerate(specs_to_use, start=1):'''
if old_body in s:
    s = s.replace(old_body, new_body, 1)
    print("ai_writer.py: body updated")
else:
    print("ai_writer.py: body pattern NOT found")

# 3. Replace remaining SECTION_SPECS reference in the loop
s = s.replace(
    "progress(f\"[{i}/{len(SECTION_SPECS)}] {title}...\")",
    "progress(f\"[{i}/{len(specs_to_use)}] {title}...\")",
    1
)

p.write_text(s, encoding="utf-8", newline="\n")
print("ai_writer.py saved")
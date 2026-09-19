from pathlib import Path

p = Path(r"D:\codeguard-ai-stage3\artifacts\codeguard-ai\backend\app\services\report_renderer\api.py")
s = p.read_text(encoding="utf-8").lstrip("\ufeff")

# 1. Add import for pdf_structure
if "from .pdf_structure import extract_structure" not in s:
    s = s.replace(
        "from .content import build_context, Section, _parse_blocks, Block",
        "from .content import build_context, Section, _parse_blocks, Block\nfrom .pdf_structure import extract_structure",
        1
    )
    print("api.py: import added")
else:
    print("api.py: import already present")

# 2. Find the AI call and add custom_headings
old_call = """        print(f"[AI] Generating sections ({_key})...", flush=True)
            ai_sections = ai_writer.generate_sections(
                _facts_from_context(ctx),
                progress=lambda m: print(m, flush=True),
            )"""
new_call = """        print(f"[AI] Generating sections ({_key})...", flush=True)
            _custom = None
            if sample_pdf:
                try:
                    _custom = extract_structure(sample_pdf)
                    if _custom:
                        print(f"[AI] Extracted {len(_custom)} headings from sample PDF", flush=True)
                    else:
                        print("[AI] Structure extraction returned 0 headings, using defaults", flush=True)
                except Exception as _e:
                    print(f"[AI] Structure extraction failed: {_e}", flush=True)
            ai_sections = ai_writer.generate_sections(
                _facts_from_context(ctx),
                progress=lambda m: print(m, flush=True),
                custom_headings=_custom,
            )"""
if old_call in s:
    s = s.replace(old_call, new_call, 1)
    print("api.py: AI call updated")
else:
    print("api.py: AI call pattern NOT found")
    print("--- searching for nearby pattern ---")
    import re
    for m in re.finditer(r"ai_writer\.generate_sections", s):
        start = max(0, m.start() - 200)
        end = min(len(s), m.end() + 200)
        print(s[start:end])
        print("---")

p.write_text(s, encoding="utf-8", newline="\n")
print("api.py saved")
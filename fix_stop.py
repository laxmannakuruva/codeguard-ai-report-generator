from pathlib import Path
p = Path(r"D:\codeguard-ai-stage3\artifacts\codeguard-ai\backend\app\services\report_renderer\pdf_structure.py")
s = p.read_text(encoding="utf-8").lstrip("\ufeff")

# Add: stop extracting after APPENDIX/APPENDICES heading
old = '''    candidates = []
    max_chapter = 0

    for l in lines:
        if l["page"] in skip_pages:
            continue'''

new = '''    candidates = []
    max_chapter = 0
    seen_appendix = False

    for l in lines:
        if seen_appendix:
            break
        if l["page"] in skip_pages:
            continue
        # Stop when we hit APPENDIX / APPENDICES / REFERENCES
        _lt = l["text"].lower().strip().rstrip(":").rstrip(".")
        if _lt in ("appendix", "appendices", "references", "bibliography"):
            seen_appendix = True
            continue'''

if old in s:
    s = s.replace(old, new, 1)
    print("pdf_structure.py: stop-at-appendix added")
else:
    print("pdf_structure.py: pattern NOT found")

p.write_text(s, encoding="utf-8", newline="\n")
print("saved")
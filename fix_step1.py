from pathlib import Path

# 1. Add ChaptersInput model
p = Path(r"D:\codeguard-ai-stage3\artifacts\codeguard-ai\backend\app\models\project.py")
s = p.read_text(encoding="utf-8")
if "class ChaptersInput" not in s:
    s += '''

class ChaptersInput(BaseModel):
    chapters: list[str] = Field(default_factory=list)
'''
    p.write_text(s, encoding="utf-8", newline="\n")
    print("project.py: ChaptersInput added")
else:
    print("project.py: already has ChaptersInput")

# 2. Add routes to report.py
p = Path(r"D:\codeguard-ai-stage3\artifacts\codeguard-ai\backend\app\routes\report.py")
s = p.read_text(encoding="utf-8").lstrip("\ufeff")

# Update import
if "ChaptersInput" not in s:
    s = s.replace(
        "from ..models.project import ProjectReport, RegenerateSectionInput, ReportSection",
        "from ..models.project import ProjectReport, RegenerateSectionInput, ReportSection, ChaptersInput",
        1
    )
    print("report.py: import updated")

# Append two new endpoints
addition = '''

@router.get("/project/{project_id}/chapters/suggest")
async def suggest_chapters(project_id: str):
    project = _project_or_404(project_id)
    if not project.sample_report_bytes:
        return {"chapters": []}
    try:
        from ..services.report_renderer.pdf_structure import extract_structure
        result = extract_structure(project.sample_report_bytes)
        return {"chapters": [c["title"] for c in result]}
    except Exception as e:
        print(f"[chapters/suggest] error: {e}", flush=True)
        return {"chapters": []}


@router.post("/project/{project_id}/chapters")
async def save_chapters(project_id: str, payload: ChaptersInput):
    project = _project_or_404(project_id)
    clean = [c.strip() for c in payload.chapters if c.strip()]
    try:
        from pathlib import Path as _P
        out = _P(project.root) / "_user_chapters.txt"
        out.write_text("\\n".join(clean), encoding="utf-8")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"saved": len(clean)}


@router.delete("/project/{project_id}/chapters")
async def clear_chapters(project_id: str):
    project = _project_or_404(project_id)
    try:
        from pathlib import Path as _P
        f = _P(project.root) / "_user_chapters.txt"
        if f.exists():
            f.unlink()
    except Exception:
        pass
    return {"cleared": True}
'''
if "chapters/suggest" not in s:
    s = s.rstrip() + addition
    p.write_text(s, encoding="utf-8", newline="\n")
    print("report.py: endpoints added")
else:
    print("report.py: endpoints already exist")

# 3. Modify api.py to read _user_chapters.txt
p = Path(r"D:\codeguard-ai-stage3\artifacts\codeguard-ai\backend\app\services\report_renderer\api.py")
s = p.read_text(encoding="utf-8").lstrip("\ufeff")

old_block = '''        _custom = None
            if sample_pdf:
                try:
                    _custom = extract_structure(sample_pdf)
                    if _custom:
                        print(f"[AI] Extracted {len(_custom)} headings from sample PDF", flush=True)
                    else:
                        print("[AI] Structure extraction returned 0 headings, using defaults", flush=True)
                except Exception as _e:
                    print(f"[AI] Structure extraction failed: {_e}", flush=True)'''

new_block = '''        _custom = None
            # User-saved chapters take priority
            if project_root:
                try:
                    from pathlib import Path as _P
                    saved = _P(project_root) / "_user_chapters.txt"
                    if saved.exists():
                        lines = [ln.strip() for ln in saved.read_text(encoding="utf-8").splitlines() if ln.strip()]
                        if lines:
                            _custom = [{"title": ln, "depth": 1} for ln in lines]
                            print(f"[AI] Using {len(_custom)} USER-SAVED chapters", flush=True)
                except Exception as _e:
                    print(f"[AI] user chapters read failed: {_e}", flush=True)
            # Otherwise extract from sample PDF
            if not _custom and sample_pdf:
                try:
                    _custom = extract_structure(sample_pdf)
                    if _custom:
                        print(f"[AI] Extracted {len(_custom)} headings from sample PDF", flush=True)
                    else:
                        print("[AI] Structure extraction returned 0 headings, using defaults", flush=True)
                except Exception as _e:
                    print(f"[AI] Structure extraction failed: {_e}", flush=True)'''

if old_block in s:
    s = s.replace(old_block, new_block, 1)
    print("api.py: user-chapters branch added")
else:
    print("api.py: pattern NOT found — check manually")

p.write_text(s, encoding="utf-8", newline="\n")

print("ALL DONE")
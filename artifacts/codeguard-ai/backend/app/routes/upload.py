from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from ..models.project import (
    ProblemStatement,
    ProblemStatementInput,
    ProjectImage,
    ProjectImages,
    ProjectReport,
    ReportGuidance,
    SampleReport,
    UploadResponse,
)
from ..services.zip_analyzer import UnsafeZipError, extract_zip_safely, new_project_id

router = APIRouter(tags=["projects"])

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}


@dataclass
class StoredProject:
    filename: str
    size_bytes: int
    root: Path
    profile: object | None = None
    guidance: ReportGuidance | None = None
    sample_report: SampleReport | None = None
    sample_report_bytes: bytes | None = None
    sample_report_text: str = ""
    report: ProjectReport | None = None
    problem_statement: str = ""
    problem_statement_updated_at: str = ""
    project_images: list[dict] = field(default_factory=list)


PROJECTS: dict[str, StoredProject] = {}


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_project(file: UploadFile = File(...)) -> UploadResponse:
    filename = file.filename or ""
    if not filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only .zip project files are accepted.")

    contents = await file.read()

    try:
        root, _ = extract_zip_safely(contents)
    except UnsafeZipError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    project_id = new_project_id()
    PROJECTS[project_id] = StoredProject(
        filename=filename,
        size_bytes=len(contents),
        root=root,
    )
    return UploadResponse(
        project_id=project_id,
        filename=filename,
        size_bytes=len(contents),
        status="uploaded",
    )


@router.post("/project/{project_id}/problem-statement", response_model=ProblemStatement)
async def save_problem_statement(
    project_id: str,
    payload: ProblemStatementInput,
) -> ProblemStatement:
    project = PROJECTS.get(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project upload not found.")

    project.problem_statement = payload.text
    project.problem_statement_updated_at = datetime.now(timezone.utc).isoformat()

    return ProblemStatement(
        project_id=project_id,
        uploaded=bool(payload.text.strip()),
        text=payload.text,
        updated_at=project.problem_statement_updated_at,
    )


@router.get("/project/{project_id}/problem-statement", response_model=ProblemStatement)
async def get_problem_statement(project_id: str) -> ProblemStatement:
    project = PROJECTS.get(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project upload not found.")
    return ProblemStatement(
        project_id=project_id,
        uploaded=bool(project.problem_statement.strip()),
        text=project.problem_statement,
        updated_at=project.problem_statement_updated_at,
    )


@router.post("/project/{project_id}/images", response_model=ProjectImages)
async def upload_project_images(
    project_id: str,
    files: list[UploadFile] = File(...),
) -> ProjectImages:
    project = PROJECTS.get(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project upload not found.")

    stored: list[dict] = []
    for f in files:
        filename = f.filename or ""
        suffix = Path(filename).suffix.lower()
        if suffix not in IMAGE_SUFFIXES:
            continue
        data = await f.read()
        if len(data) > 8 * 1024 * 1024:
            continue
        project.project_images.append({
            "filename": filename,
            "data": data,
            "content_type": f.content_type or "image/png",
        })
        try:
            from pathlib import Path as _P
            disk_dir = _P(project.root) / "_user_uploads"
            disk_dir.mkdir(exist_ok=True, parents=True)
            safe_name = filename.replace("/", "_").replace("\\", "_") or "image.png"
            (disk_dir / safe_name).write_bytes(data)
        except Exception:
            pass
        try:
            from pathlib import Path as _P
            disk_dir = _P(project.root) / "_user_uploads"
            disk_dir.mkdir(exist_ok=True, parents=True)
            safe_name = filename.replace("/", "_").replace("\\", "_") or "image.png"
            (disk_dir / safe_name).write_bytes(data)
        except Exception:
            pass
        stored.append({
            "project_id": project_id,
            "filename": filename,
            "size_bytes": len(data),
            "content_type": f.content_type or "image/png",
            "caption": Path(filename).stem.replace("_", " ").replace("-", " "),
        })

    return ProjectImages(
        project_id=project_id,
        images=[ProjectImage(**s) for s in stored],
    )


@router.get("/project/{project_id}/images", response_model=ProjectImages)
async def list_project_images(project_id: str) -> ProjectImages:
    project = PROJECTS.get(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project upload not found.")

    return ProjectImages(
        project_id=project_id,
        images=[
            ProjectImage(
                project_id=project_id,
                filename=img["filename"],
                size_bytes=len(img["data"]),
                content_type=img["content_type"],
                caption=Path(img["filename"]).stem.replace("_", " ").replace("-", " "),
            )
            for img in project.project_images
        ],
    )
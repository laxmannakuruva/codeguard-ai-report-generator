import io

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from pypdf import PdfReader

from ..models.project import (
    ProjectProfile,
    ReportGuidance,
    ReportGuidanceInput,
    ReportInputs,
    SampleReport,
)
from .upload import PROJECTS
from ..services.project_profiler import profile_project

router = APIRouter(tags=["projects"])
MAX_SAMPLE_REPORT_BYTES = 10 * 1024 * 1024
ALLOWED_SAMPLE_EXTENSIONS = {".pdf", ".doc", ".docx", ".txt", ".md"}
TEXT_SAMPLE_EXTENSIONS = {".txt", ".md"}
MAX_SAMPLE_TEXT_CHARS = 6000


def _project_or_404(project_id: str):
    project = PROJECTS.get(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project upload not found.")
    return project


def _empty_guidance(project_id: str) -> ReportGuidance:
    return ReportGuidance(
        project_id=project_id,
        instructions="",
        status="not_configured",
    )


def _empty_sample_report(project_id: str) -> SampleReport:
    return SampleReport(
        project_id=project_id,
        uploaded=False,
        filename="",
        size_bytes=0,
        content_type="",
        status="not_uploaded",
        text_preview="",
    )


@router.post("/analyze/{project_id}", response_model=ProjectProfile)
async def analyze_project(project_id: str) -> ProjectProfile:
    project = _project_or_404(project_id)
    try:
        profile = profile_project(project.root, project_id)
    except OSError as error:
        raise HTTPException(status_code=422, detail="The project could not be analyzed.") from error
    project.profile = profile
    return profile


@router.get("/project/{project_id}", response_model=ProjectProfile)
async def get_project(project_id: str) -> ProjectProfile:
    project = _project_or_404(project_id)
    if project.profile is None:
        raise HTTPException(status_code=409, detail="Project analysis has not been run yet.")
    return project.profile


@router.post("/project/{project_id}/report-guidance", response_model=ReportGuidance)
async def save_report_guidance(
    project_id: str,
    payload: ReportGuidanceInput,
) -> ReportGuidance:
    project = _project_or_404(project_id)
    guidance = ReportGuidance(
        project_id=project_id,
        instructions=payload.instructions.strip(),
        status="saved",
    )
    if not guidance.instructions:
        raise HTTPException(status_code=422, detail="Report instructions cannot be blank.")
    project.guidance = guidance
    return guidance


@router.post(
    "/project/{project_id}/sample-report",
    response_model=SampleReport,
    status_code=status.HTTP_201_CREATED,
)
async def upload_sample_report(
    project_id: str,
    file: UploadFile = File(...),
) -> SampleReport:
    project = _project_or_404(project_id)
    filename = file.filename or ""
    extension = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    normalized_extension = f".{extension}" if extension else ""
    if normalized_extension not in ALLOWED_SAMPLE_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Sample reports must be PDF, DOC, DOCX, TXT, or Markdown files.",
        )

    contents = await file.read(MAX_SAMPLE_REPORT_BYTES + 1)
    if len(contents) > MAX_SAMPLE_REPORT_BYTES:
        raise HTTPException(status_code=413, detail="Sample reports must be smaller than 10 MB.")
    if not contents:
        raise HTTPException(status_code=400, detail="The sample report is empty.")

    try:
        if normalized_extension == ".pdf":
            extracted_text = "\n\n".join(
                page.extract_text() or ""
                for page in PdfReader(io.BytesIO(contents)).pages
            ).strip()
        elif normalized_extension in TEXT_SAMPLE_EXTENSIONS:
            extracted_text = contents.decode("utf-8", errors="replace").strip()
        else:
            extracted_text = ""
    except Exception as error:
        raise HTTPException(status_code=400, detail="The sample PDF could not be read.") from error

    extracted_text = extracted_text[:MAX_SAMPLE_TEXT_CHARS]
    text_preview = extracted_text[:1200]

    sample_report = SampleReport(
        project_id=project_id,
        uploaded=True,
        filename=filename,
        size_bytes=len(contents),
        content_type=file.content_type or "application/octet-stream",
        status="uploaded",
        text_preview=text_preview,
    )
    project.sample_report = sample_report
    project.sample_report_bytes = contents
    project.sample_report_text = extracted_text
    return sample_report


@router.get("/project/{project_id}/report-inputs", response_model=ReportInputs)
async def get_report_inputs(project_id: str) -> ReportInputs:
    project = _project_or_404(project_id)
    return ReportInputs(
        project_id=project_id,
        guidance=project.guidance or _empty_guidance(project_id),
        sample_report=project.sample_report or _empty_sample_report(project_id),
    )
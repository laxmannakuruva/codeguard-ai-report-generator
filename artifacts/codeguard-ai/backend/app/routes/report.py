import asyncio

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from ..models.project import ProjectReport, RegenerateSectionInput, ReportSection
from ..services.report_generator import build_context, generate_section, plan_sections, regenerate_section
from ..services.report_pdf import render_report_pdf
from .upload import PROJECTS, StoredProject

router = APIRouter(tags=["projects"])


def _project_or_404(project_id: str) -> StoredProject:
    project = PROJECTS.get(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project upload not found.")
    return project


def _sample_text(project: StoredProject) -> str:
    sample = project.sample_report
    if sample is None or not sample.uploaded:
        return ""
    return project.sample_report_text or sample.text_preview or ""


def _context(project: StoredProject):
    if project.profile is None:
        raise HTTPException(status_code=409, detail="Project analysis has not been run yet.")
    instructions = project.guidance.instructions if project.guidance else ""
    problem = getattr(project, "problem_statement", "") or ""
    context = build_context(project.profile, instructions, _sample_text(project))
    if problem:
        context["problem_statement"] = problem
    return context


@router.post("/project/{project_id}/report", response_model=ProjectReport)
async def generate_report(project_id: str) -> ProjectReport:
    project = _project_or_404(project_id)
    context = _context(project)

    planned = await asyncio.to_thread(plan_sections, context)
    contents = await asyncio.gather(
        *(asyncio.to_thread(generate_section, title, context) for _, title in planned)
    )
    sections = [
        ReportSection(id=section_id, title=title, content=content, order=index)
        for index, ((section_id, title), content) in enumerate(zip(planned, contents))
    ]

    report = ProjectReport(project_id=project_id, status="generated", sections=sections)
    project.report = report
    return report


@router.get("/project/{project_id}/report", response_model=ProjectReport)
async def get_report(project_id: str) -> ProjectReport:
    project = _project_or_404(project_id)
    if project.report is None:
        return ProjectReport(project_id=project_id, status="not_generated", sections=[])
    return project.report


@router.get("/project/{project_id}/report.pdf")
async def download_report_pdf(project_id: str) -> Response:
    project = _project_or_404(project_id)
    if project.profile is None:
        raise HTTPException(status_code=409, detail="Project analysis has not been run yet.")
    if project.report is None or not project.report.sections:
        raise HTTPException(status_code=409, detail="The report has not been generated yet.")

    # Build problem statement section if one was saved
    problem_statement = getattr(project, "problem_statement", "") or ""
    problem_section = None
    if problem_statement.strip():
        problem_section = ReportSection(
            id="problem-statement",
            title="Problem Statement",
            content=problem_statement.strip(),
            order=0,
        )

    sections_for_pdf = list(project.report.sections)
    if problem_section:
        # Insert Problem Statement right after Abstract, or at the front if no Abstract
        insert_at = 0
        for i, s in enumerate(sections_for_pdf):
            if s.title.strip().lower() == "abstract":
                insert_at = i + 1
                break
        sections_for_pdf.insert(insert_at, problem_section)

    pdf = await asyncio.to_thread(
        render_report_pdf,
        project.profile,
        sections_for_pdf,
        project.sample_report_bytes,
        project.root,
    )
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=project-report.pdf"},
    )


@router.post(
    "/project/{project_id}/report/sections/{section_id}/regenerate",
    response_model=ReportSection,
)
async def regenerate_report_section(
    project_id: str,
    section_id: str,
    payload: RegenerateSectionInput | None = None,
) -> ReportSection:
    project = _project_or_404(project_id)
    if project.report is None:
        raise HTTPException(status_code=409, detail="The report has not been generated yet.")

    existing = next(
        (section for section in project.report.sections if section.id == section_id), None
    )
    if existing is None:
        raise HTTPException(status_code=404, detail="Report section not found.")

    context = _context(project)
    previous = (payload.content if payload else "") or existing.content

    content = regenerate_section(existing.title, context, previous)

    updated = ReportSection(
        id=existing.id, title=existing.title, content=content, order=existing.order
    )
    project.report.sections = [
        updated if section.id == section_id else section for section in project.report.sections
    ]
    return updated
from typing import Any

from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    project_id: str
    filename: str
    size_bytes: int
    status: str


class ProjectProfile(BaseModel):
    project_id: str
    project_name: str
    project_type: str
    languages: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    libraries: list[str] = Field(default_factory=list)
    frontend: str
    backend: str
    database: str
    apis: list[str] = Field(default_factory=list)
    modules: list[str] = Field(default_factory=list)
    features: list[str] = Field(default_factory=list)
    entry_points: list[str] = Field(default_factory=list)
    readme_summary: str
    folder_structure: dict[str, Any] = Field(default_factory=dict)
    tests: list[str] = Field(default_factory=list)
    important_files: list[str] = Field(default_factory=list)


class ReportGuidanceInput(BaseModel):
    instructions: str = Field(min_length=1, max_length=10_000)


class ReportGuidance(BaseModel):
    project_id: str
    instructions: str
    status: str


class SampleReport(BaseModel):
    project_id: str
    uploaded: bool
    filename: str
    size_bytes: int
    content_type: str
    status: str
    text_preview: str


class ProblemStatement(BaseModel):
    project_id: str
    uploaded: bool
    text: str = ""
    updated_at: str = ""


class ProblemStatementInput(BaseModel):
    text: str = Field(default="", max_length=20_000)


class ProjectImage(BaseModel):
    project_id: str
    filename: str
    size_bytes: int
    content_type: str
    caption: str = ""


class ProjectImages(BaseModel):
    project_id: str
    images: list[ProjectImage] = Field(default_factory=list)


class ReportInputs(BaseModel):
    project_id: str
    guidance: ReportGuidance
    sample_report: SampleReport


class ReportSection(BaseModel):
    id: str
    title: str
    content: str
    order: int


class ProjectReport(BaseModel):
    project_id: str
    status: str
    sections: list[ReportSection] = Field(default_factory=list)


class RegenerateSectionInput(BaseModel):
    content: str = Field(default="", max_length=20_000)

class ChaptersInput(BaseModel):
    chapters: list[str] = Field(default_factory=list)

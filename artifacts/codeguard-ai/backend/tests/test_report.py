"""Stage 3 backend tests: grounded report generation endpoints."""

from __future__ import annotations

import io
import zipfile

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.routes import report as report_routes
from backend.app.services import report_generator


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    return TestClient(app)


def _zip_bytes() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("demo/README.md", "# Demo\n\nA small FastAPI demo project.")
        archive.writestr("demo/main.py", "from fastapi import FastAPI\napp = FastAPI()\n")
        archive.writestr("demo/requirements.txt", "fastapi\n")
    return buffer.getvalue()


def _pdf_bytes() -> bytes:
    objects = [
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj",
        b"2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj",
        b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 300 144]/Resources<</Font<</F1 5 0 R>>>>/Contents 4 0 R>>endobj",
        b"4 0 obj<</Length 62>>stream\nBT /F1 12 Tf 20 100 Td (Sample PDF heading) Tj ET\nendstream\nendobj",
        b"5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj",
    ]
    header = b"%PDF-1.4\n"
    body = bytearray(header)
    offsets = [0]
    for obj in objects:
        offsets.append(len(body))
        body.extend(obj + b"\n")
    xref = len(body)
    body.extend(f"xref\n0 {len(objects) + 1}\n".encode())
    body.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        body.extend(f"{offset:010d} 00000 n \n".encode())
    body.extend(
        f"trailer<</Size {len(objects) + 1}/Root 1 0 R>>\nstartxref\n{xref}\n%%EOF\n".encode()
    )
    return bytes(body)


def _uploaded_project(client: TestClient) -> str:
    response = client.post(
        "/api/upload", files={"file": ("demo.zip", _zip_bytes(), "application/zip")}
    )
    assert response.status_code == 201
    project_id = response.json()["project_id"]
    assert client.post(f"/api/analyze/{project_id}").status_code == 200
    return project_id


def test_report_is_not_generated_initially(client: TestClient) -> None:
    project_id = _uploaded_project(client)
    response = client.get(f"/api/project/{project_id}/report")
    assert response.status_code == 200
    assert response.json() == {
        "project_id": project_id,
        "status": "not_generated",
        "sections": [],
    }


def test_generate_report_uses_profile_and_instructions(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    project_id = _uploaded_project(client)
    client.post(
        f"/api/project/{project_id}/report-guidance",
        json={"instructions": "Follow the university format with an abstract."},
    )
    response = client.post(f"/api/project/{project_id}/report")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "generated"
    assert len(body["sections"]) >= 5
    assert body["sections"][0]["order"] == 0
    assert all(section["content"] for section in body["sections"])
    assert "Follow the university format" not in body["sections"][0]["content"]

    stored = client.get(f"/api/project/{project_id}/report").json()
    assert stored["sections"] == body["sections"]


def test_sample_report_is_used_for_structure_only(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    project_id = _uploaded_project(client)
    client.post(
        f"/api/project/{project_id}/sample-report",
        files={"file": ("sample.md", b"# Abstract\n\nSecret Corp built a payroll system.", "text/markdown")},
    )
    response = client.post(f"/api/project/{project_id}/report")
    assert response.status_code == 200
    assert response.json()["sections"]


def test_pdf_sample_text_is_extracted_and_used(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    project_id = _uploaded_project(client)
    upload = client.post(
        f"/api/project/{project_id}/sample-report",
        files={"file": ("sample.pdf", _pdf_bytes(), "application/pdf")},
    )
    assert upload.status_code == 201
    assert "Sample PDF heading" in upload.json()["text_preview"]

    response = client.post(f"/api/project/{project_id}/report")
    assert response.status_code == 200
    assert response.json()["status"] == "generated"


def test_generated_report_can_be_downloaded_as_pdf(client: TestClient) -> None:
    project_id = _uploaded_project(client)
    client.post(
        f"/api/project/{project_id}/sample-report",
        files={"file": ("sample.pdf", _pdf_bytes(), "application/pdf")},
    )
    assert client.post(f"/api/project/{project_id}/report").status_code == 200

    response = client.get(f"/api/project/{project_id}/report.pdf")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF-")


def test_missing_information_is_marked_not_detected(client: TestClient) -> None:
    project_id = _uploaded_project(client)
    profile = client.get(f"/api/project/{project_id}").json()

    class Blank:
        pass

    facts = report_generator.build_facts(Blank())
    assert "Not detected" in facts
    assert profile["project_id"] == project_id


def test_regenerate_single_section(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    project_id = _uploaded_project(client)
    sections = client.post(f"/api/project/{project_id}/report").json()["sections"]
    target = sections[1]

    response = client.post(
        f"/api/project/{project_id}/report/sections/{target['id']}/regenerate",
        json={"content": target["content"]},
    )
    assert response.status_code == 200
    updated = response.json()
    assert updated["id"] == target["id"]
    assert updated["title"] == target["title"]
    assert updated["content"]

    stored = client.get(f"/api/project/{project_id}/report").json()["sections"]
    assert stored[1]["content"] == updated["content"]
    assert stored[0]["content"]


def test_unknown_section_returns_404(client: TestClient) -> None:
    project_id = _uploaded_project(client)
    client.post(f"/api/project/{project_id}/report")
    response = client.post(
        f"/api/project/{project_id}/report/sections/nope/regenerate", json={"content": ""}
    )
    assert response.status_code == 404


def test_generation_works_without_api_key(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    project_id = _uploaded_project(client)
    response = client.post(f"/api/project/{project_id}/report")
    assert response.status_code == 200


def test_unknown_project_returns_404(client: TestClient) -> None:
    assert client.post("/api/project/missing/report").status_code == 404


def test_report_requires_analysis(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    upload = client.post(
        "/api/upload", files={"file": ("demo.zip", _zip_bytes(), "application/zip")}
    ).json()
    response = client.post(f"/api/project/{upload['project_id']}/report")
    assert response.status_code == 409


def test_stage_one_and_two_endpoints_still_work(client: TestClient) -> None:
    project_id = _uploaded_project(client)
    assert client.get("/api/health").json() == {"status": "ok"}
    assert client.get(f"/api/project/{project_id}").status_code == 200
    guidance = client.post(
        f"/api/project/{project_id}/report-guidance", json={"instructions": "Keep it formal."}
    )
    assert guidance.status_code == 200
    inputs = client.get(f"/api/project/{project_id}/report-inputs").json()
    assert inputs["guidance"]["instructions"] == "Keep it formal."
    assert inputs["sample_report"]["uploaded"] is False

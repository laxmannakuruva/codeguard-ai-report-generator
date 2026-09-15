# CodeGuard AI

CodeGuard AI is a project understanding workspace for B.Tech and college students. Upload a software project as a ZIP and the app safely inspects its real files to produce a structured project profile and a professional summary dashboard.

The first two stages are intentionally grounded and non-generative: the app does not create reports, export PDF/DOCX files, scan for vulnerabilities, detect bugs, run linters, or execute uploaded code. Technologies and features are shown only when supported by files found in the uploaded project.

## Architecture

- **Frontend:** React + Vite in the artifact root (`src/`). It provides drag-and-drop upload, progress states, error handling, and the summary dashboard.
- **Backend:** FastAPI in `backend/app/`. ZIP extraction, file inspection, manifest parsing, and profiling are separated into route, model, and service modules.
- **API:** The frontend and backend are routed through `/api`. Uploaded projects are held in temporary server memory for the current first-stage session; no uploaded code is persisted in a database.
- **Report inputs:** Stage 2 stores report instructions and sample-report bytes separately from the `ProjectProfile`, so later report generation can consume both without changing the analyzed project facts.
- **Safety:** Only ZIP files are accepted. Archives are bounded by entry count and total uncompressed size. Absolute paths, parent traversal, and symbolic links are rejected. Uploaded files are read as text/configuration only and are never executed.

The Replit artifact uses the project root as the Vite frontend package and keeps the requested FastAPI `backend/` structure beside it so the app remains runnable through the workspace's managed frontend workflow.

## Run the backend

From the `artifacts/codeguard-ai` directory:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

The API is available at `/api` when routed through the workspace proxy. For a direct local FastAPI process, the same routes are available under `http://localhost:8000/api`.

## Run the frontend

From the repository root:

```bash
pnpm install
pnpm --filter @workspace/codeguard-ai run dev
```

The Vite server uses the port and base path supplied by the Replit artifact workflow. In the hosted preview, the shared router sends `/api/*` requests to FastAPI and the remaining paths to Vite.

## API endpoints

### `GET /api/health`

Returns `{ "status": "ok" }`.

### `POST /api/upload`

Accepts a multipart form field named `file`. The file must be a valid `.zip` archive.

Returns:

```json
{
  "project_id": "generated-id",
  "filename": "my-project.zip",
  "size_bytes": 12345,
  "status": "uploaded"
}
```

### `POST /api/analyze/{project_id}`

Safely analyzes the uploaded project and returns a `ProjectProfile` containing project name/type, languages, frameworks, dependencies, frontend/backend/database evidence, API evidence, modules, features, entry points, README summary, folder structure, tests, and important files.

### `GET /api/project/{project_id}`

Returns the completed profile for a previously analyzed upload.

### `POST /api/project/{project_id}/report-guidance`

Accepts JSON with an `instructions` string up to 10,000 characters and saves the student's required report format, tone, sections, or academic guidelines separately from the project profile.

### `POST /api/project/{project_id}/sample-report`

Accepts a multipart field named `file`. Supported formats are PDF, DOC, DOCX, TXT, and Markdown files up to 10 MB. The response includes file metadata and a text preview for plain-text samples.

### `GET /api/project/{project_id}/report-inputs`

Returns the current report instructions and sample-report metadata. Before Stage 2 input is provided, it returns explicit `not_configured` and `not_uploaded` states.

## Current implemented features

- ZIP file selection and drag-and-drop upload
- Filename and file size display
- Upload and analysis progress/loading states
- Invalid file, unsafe archive, size limit, and API error states
- Real project extraction and inspection
- Evidence-based detection from source extensions, package manifests, dependency files, build files, README files, and configuration
- Project summary dashboard with technology, components, structure, README, and important-file sections
- Report instructions form with character count and saved state
- Sample report upload for PDF, DOC, DOCX, TXT, and Markdown files
- Separate report-inputs API response for later report generation
- Responsive UI with empty, loading, success, and error states

## Planned future stages

1. AI project report generation
2. Report preview and editing
3. PDF/DOCX export
4. Cloud deployment

Those stages are not part of the current implementation.
## Stage 3 — AI report generation

- `POST /api/project/{project_id}/report` generates the full report section by section.
- `GET /api/project/{project_id}/report` returns the current report (`status: not_generated` before the first run).
- `POST /api/project/{project_id}/report/sections/{section_id}/regenerate` rewrites one section.

Generation is grounded in the analyzed `ProjectProfile` plus the saved report
instructions. Facts that were not detected in the uploaded project are written
as `Not detected`; information the user did not supply is written as
`Not provided`. An uploaded sample report influences structure, order, style and
level of detail only — never project-specific content.

Report generation runs locally from the analyzed project profile and the
uploaded sample report structure. It requires no API key and returns explicit
`Not detected` or `Not provided` markers for missing information.

Backend tests: `pip install -r backend/requirements.txt -r backend/requirements-dev.txt`
then `pytest backend/tests` from the artifact root.

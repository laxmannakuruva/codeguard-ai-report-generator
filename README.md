# CodeGuard AI

AI-powered project report generator. Upload a ZIP of any project, and get back a professionally formatted academic report PDF — with chapters, tables, TOC, and AI-written narrative.

## What it does

- **Upload a project ZIP** — the system extracts the project name, languages, frameworks, modules, features, and entry points.
- **Optionally upload a sample report PDF** — its structure (chapters, ordering) becomes the template for your generated report.
- **Add a problem statement** — typed text that becomes a chapter in the final report.
- **Upload project images** — screenshots, diagrams, or photos to embed as figures.
- **Generate the report** — AI writes the narrative (locally via Ollama, no cloud API needed), and the final PDF is rendered with Playwright + Chromium.

## Stack

**Backend:** Python 3.14 · FastAPI · PyMuPDF · Jinja2 · Playwright · Ollama (llama3.1:8b)

**Frontend:** React · Vite · TypeScript · TailwindCSS

**Monorepo:** pnpm workspaces

## Project layout

``nartifacts/
  codeguard-ai/
    backend/
      app/
        models/       Pydantic models
        routes/       FastAPI endpoints (upload, project, report)
        services/
          report_renderer/   PDF engine (design + AI writer + Playwright)
    src/
      components/
        report-studio.tsx
        welcome-overlay.tsx
      hooks/
      pages/
        home.tsx      the three-stage UI
  api-server/
lib/
``n
## Running locally

1. Install Python dependencies:
   ``n   python -m venv .venv
   .venv\Scripts\activate
   pip install -r artifacts/codeguard-ai/backend/requirements.txt
   playwright install chromium
   ``n
2. Install Node dependencies:
   ``n   pnpm install
   ``n
3. Start Ollama with a writing model:
   ``n   ollama pull llama3.1:8b
   ollama serve
   ``n
4. Run the backend:
   ``n   cd artifacts/codeguard-ai/backend
   uvicorn app.main:app --port 8000 --reload
   ``n
5. Run the frontend:
   ``n   cd artifacts/codeguard-ai
   pnpm run dev
   ``n
6. Open `http://localhost:5000`

## How the report engine works

1. **Design source** — the sample report PDF. We extract page size, margins, fonts, colors, and chapter outline.
2. **Content source** — the project ZIP. We extract facts only; the ZIP's code is never executed.
3. **Narrative source** — Ollama writes each section using only the extracted facts. No invented names, dates, or metrics.
4. **Renderer** — Jinja2 HTML → Playwright Chromium → A4 PDF.

## License

MIT



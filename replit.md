# CodeGuard AI

CodeGuard AI safely understands an uploaded software project and turns its real files into a grounded project summary for students.

## Run & Operate

- `pnpm --filter @workspace/codeguard-ai run dev` — run the React/Vite frontend
- `uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000` from `artifacts/codeguard-ai` — run the FastAPI backend
- `pnpm run typecheck` — full typecheck across all packages
- `pnpm run build` — typecheck + build all packages
- `pnpm --filter @workspace/api-spec run codegen` — regenerate API hooks and Zod schemas from the OpenAPI spec
- `pnpm --filter @workspace/db run push` — push DB schema changes (dev only)
- Required env: `DATABASE_URL` — Postgres connection string

## Stack

- pnpm workspaces, Node.js 24, TypeScript 5.9
- Frontend: React + Vite
- Backend: Python + FastAPI
- API contract: OpenAPI + Orval-generated client types

## Where things live

- `artifacts/codeguard-ai/src/` — React/Vite frontend and summary dashboard
- `artifacts/codeguard-ai/backend/app/` — FastAPI routes, ZIP safety, and evidence-based profiler
- `artifacts/codeguard-ai/README.md` — product README, API reference, and future stages
- `lib/api-spec/openapi.yaml` — shared API contract used for generated client types

## Architecture decisions

- Uploaded archives are analyzed as text/configuration only; uploaded code is never executed.
- The first stage keeps profiles in temporary server memory rather than adding persistence before the product needs it.
- Unknown values are returned explicitly as `Not detected` rather than inferred from common project conventions.

## Product

Students can upload a ZIP by browsing or dragging it into the app, review detected project identity, technologies, modules, features, APIs, entry points, tests, README context, important files, and a readable folder tree, then add report instructions and a sample report for the later generation stage.

## User preferences

The current build intentionally excludes AI report generation, PDF/DOCX export, bug detection, security scanning, linters, and vulnerability analysis.

## Gotchas

- The original generic API scaffold is on `/legacy-api` so CodeGuard AI can own `/api` without route collisions.
- `lib/api-spec/openapi.yaml` must be regenerated with `pnpm --filter @workspace/api-spec run codegen` after contract changes.

## Pointers

- See the `pnpm-workspace` skill for workspace structure, TypeScript setup, and package details

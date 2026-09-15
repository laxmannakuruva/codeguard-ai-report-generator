from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes.project import router as project_router
from .routes.report import router as report_router
from .routes.upload import router as upload_router

app = FastAPI(
    title="CodeGuard AI",
    description="Grounded project understanding API for uploaded ZIP projects.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router, prefix="/api")
app.include_router(project_router, prefix="/api")
app.include_router(report_router, prefix="/api")


@app.get("/api/health")
@app.get("/api/healthz")
async def health() -> dict[str, str]:
    return {"status": "ok"}
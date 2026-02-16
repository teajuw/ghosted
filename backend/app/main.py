from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import health, scan, clean, detect, compare, experiment

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Don't let invisible characters decide your grade.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(scan.router, prefix="/api/v1", tags=["scan"])
app.include_router(clean.router, prefix="/api/v1", tags=["clean"])
app.include_router(detect.router, prefix="/api/v1", tags=["detect"])
app.include_router(compare.router, prefix="/api/v1", tags=["compare"])
app.include_router(experiment.router, prefix="/api/v1", tags=["experiment"])

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings

app = FastAPI(
    title="Allergy Tracker API",
    description="Backend API for personal allergy symptom monitoring and ASIT tracking.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def read_root():
    return {
        "message": "Allergy Tracker API is running",
        "status": "ok",
    }
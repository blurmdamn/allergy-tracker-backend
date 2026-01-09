from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router

app = FastAPI(
    title="Allergy Tracker API",
    description="Backend API for PWA Seasonal Allergy Monitoring.",
    version="0.1.0"
)

# CORS (пока можно разрешить всё для разработки)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "Allergy Tracker API is Running!", "status": "ok"}

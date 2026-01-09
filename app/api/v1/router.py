from fastapi import APIRouter
from .health import router as health_router
from .dict import router as dict_router

api_router = APIRouter()

api_router.include_router(health_router, tags=["Health"])
api_router.include_router(dict_router)
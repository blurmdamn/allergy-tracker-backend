from fastapi import APIRouter

from .allergy import router as allergy_router
from .asit import router as asit_router
from .auth import router as auth_router
from .checkins import router as checkins_router
from .dict import router as dict_router
from .health import router as health_router
from .medications import router as medications_router
from .profiles import router as profiles_router
from .reminders import router as reminders_router
from .reports import router as reports_router

api_router = APIRouter()

api_router.include_router(health_router, tags=["Health"])
api_router.include_router(dict_router)
api_router.include_router(auth_router)

api_router.include_router(profiles_router)
api_router.include_router(allergy_router)
api_router.include_router(asit_router)
api_router.include_router(medications_router)
api_router.include_router(reminders_router)
api_router.include_router(checkins_router)
api_router.include_router(reports_router)
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_user
from app.models.users import User
from app.models.profiles import PatientProfile
from app.schemas.profiles import ProfileOut, ProfileUpdate

router = APIRouter(prefix="/me", tags=["Me"])


@router.get("/profile", response_model=ProfileOut)
async def get_my_profile(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(PatientProfile).where(PatientProfile.user_id == user.id))
    profile = res.scalar_one_or_none()

    if not profile:
        # профиль ещё не создан — отдаём пустое
        return ProfileOut(full_name=None, birth_date=None, sex=None)

    return ProfileOut(
        full_name=profile.full_name,
        birth_date=profile.birth_date,
        sex=profile.sex,
    )


@router.put("/profile", response_model=ProfileOut)
async def update_my_profile(
    payload: ProfileUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(PatientProfile).where(PatientProfile.user_id == user.id))
    profile = res.scalar_one_or_none()

    if not profile:
        profile = PatientProfile(user_id=user.id)
        db.add(profile)

    # обновляем только то, что пришло (None = "не менять")
    if payload.full_name is not None:
        profile.full_name = payload.full_name
    if payload.birth_date is not None:
        profile.birth_date = payload.birth_date
    if payload.sex is not None:
        profile.sex = payload.sex

    await db.commit()
    await db.refresh(profile)

    return ProfileOut(
        full_name=profile.full_name,
        birth_date=profile.birth_date,
        sex=profile.sex,
    )

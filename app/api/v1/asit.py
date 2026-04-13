from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.asit import AsitEvent, AsitPlan
from app.models.dicts import Allergen, Medication
from app.models.users import User
from app.schemas.asit import (
    AsitEventCreate,
    AsitEventOut,
    AsitEventUpdate,
    AsitPlanCreate,
    AsitPlanOut,
    AsitPlanUpdate,
)

router = APIRouter(prefix="/me/asit", tags=["ASIT"])

ALLOWED_REGIMENS = {"conventional", "daily", "accelerated"}
ALLOWED_EVENT_STATUSES = {"planned", "done", "skipped", "rescheduled"}


async def _get_owned_plan_or_404(
    plan_id: int,
    user_id: int,
    db: AsyncSession,
) -> AsitPlan:
    res = await db.execute(
        select(AsitPlan).where(
            AsitPlan.id == plan_id,
            AsitPlan.user_id == user_id,
        )
    )
    plan = res.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="ASIT plan not found")
    return plan


async def _get_owned_event_or_404(
    event_id: int,
    user_id: int,
    db: AsyncSession,
) -> AsitEvent:
    res = await db.execute(
        select(AsitEvent)
        .join(AsitPlan, AsitPlan.id == AsitEvent.plan_id)
        .where(
            AsitEvent.id == event_id,
            AsitPlan.user_id == user_id,
        )
    )
    event = res.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="ASIT event not found")
    return event


async def _resolve_allergen_id(code: str | None, db: AsyncSession) -> int | None:
    if not code:
        return None

    res = await db.execute(select(Allergen).where(Allergen.code == code))
    allergen = res.scalar_one_or_none()
    if not allergen:
        raise HTTPException(status_code=400, detail=f"Unknown allergen code: {code}")
    return allergen.id


async def _resolve_medication_id(code: str | None, db: AsyncSession) -> int | None:
    if not code:
        return None

    res = await db.execute(select(Medication).where(Medication.code == code))
    medication = res.scalar_one_or_none()
    if not medication:
        raise HTTPException(status_code=400, detail=f"Unknown medication code: {code}")
    return medication.id


async def _get_allergen_code_by_id(allergen_id: int | None, db: AsyncSession) -> str | None:
    if allergen_id is None:
        return None

    res = await db.execute(select(Allergen.code).where(Allergen.id == allergen_id))
    return res.scalar_one_or_none()


async def _get_medication_code_by_id(medication_id: int | None, db: AsyncSession) -> str | None:
    if medication_id is None:
        return None

    res = await db.execute(select(Medication.code).where(Medication.id == medication_id))
    return res.scalar_one_or_none()


async def _serialize_plan(plan: AsitPlan, db: AsyncSession) -> AsitPlanOut:
    return AsitPlanOut(
        id=plan.id,
        regimen=plan.regimen,
        target_allergen_code=await _get_allergen_code_by_id(plan.target_allergen_id, db),
        medication_code=await _get_medication_code_by_id(plan.medication_id, db),
        interval_days=plan.interval_days,
        dose_unit=plan.dose_unit,
        started_at=plan.started_at,
        is_active=plan.is_active,
    )


@router.get("/plans", response_model=list[AsitPlanOut])
async def list_my_asit_plans(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(AsitPlan)
        .where(AsitPlan.user_id == user.id)
        .order_by(AsitPlan.is_active.desc(), AsitPlan.created_at.desc(), AsitPlan.id.desc())
    )
    plans = list(res.scalars().all())

    result: list[AsitPlanOut] = []
    for plan in plans:
        result.append(await _serialize_plan(plan, db))
    return result


@router.post("/plans", response_model=AsitPlanOut)
async def create_my_asit_plan(
    payload: AsitPlanCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if payload.regimen not in ALLOWED_REGIMENS:
        raise HTTPException(
            status_code=400,
            detail="regimen must be one of: conventional, daily, accelerated",
        )

    if payload.interval_days is not None and payload.interval_days < 1:
        raise HTTPException(status_code=400, detail="interval_days must be >= 1")

    allergen_id = await _resolve_allergen_id(payload.target_allergen_code, db)
    medication_id = await _resolve_medication_id(payload.medication_code, db)

    plan = AsitPlan(
        user_id=user.id,
        regimen=payload.regimen,
        target_allergen_id=allergen_id,
        medication_id=medication_id,
        interval_days=payload.interval_days,
        dose_unit=payload.dose_unit,
        started_at=payload.started_at,
        is_active=True,
    )
    db.add(plan)
    await db.commit()
    await db.refresh(plan)

    return await _serialize_plan(plan, db)


@router.get("/plans/{plan_id}", response_model=AsitPlanOut)
async def get_my_asit_plan(
    plan_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    plan = await _get_owned_plan_or_404(plan_id=plan_id, user_id=user.id, db=db)
    return await _serialize_plan(plan, db)


@router.patch("/plans/{plan_id}", response_model=AsitPlanOut)
async def update_my_asit_plan(
    plan_id: int,
    payload: AsitPlanUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    plan = await _get_owned_plan_or_404(plan_id=plan_id, user_id=user.id, db=db)

    if payload.regimen is not None:
        if payload.regimen not in ALLOWED_REGIMENS:
            raise HTTPException(
                status_code=400,
                detail="regimen must be one of: conventional, daily, accelerated",
            )
        plan.regimen = payload.regimen

    if payload.interval_days is not None:
        if payload.interval_days < 1:
            raise HTTPException(status_code=400, detail="interval_days must be >= 1")
        plan.interval_days = payload.interval_days

    if payload.dose_unit is not None:
        plan.dose_unit = payload.dose_unit

    if payload.started_at is not None:
        plan.started_at = payload.started_at

    if payload.is_active is not None:
        plan.is_active = payload.is_active

    if payload.target_allergen_code is not None:
        plan.target_allergen_id = await _resolve_allergen_id(payload.target_allergen_code, db)

    if payload.medication_code is not None:
        plan.medication_id = await _resolve_medication_id(payload.medication_code, db)

    await db.commit()
    await db.refresh(plan)

    return await _serialize_plan(plan, db)


@router.get("/plans/{plan_id}/events", response_model=list[AsitEventOut])
async def list_my_asit_plan_events(
    plan_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_owned_plan_or_404(plan_id=plan_id, user_id=user.id, db=db)

    res = await db.execute(
        select(AsitEvent)
        .where(AsitEvent.plan_id == plan_id)
        .order_by(AsitEvent.planned_date.asc(), AsitEvent.id.asc())
    )
    events = res.scalars().all()
    return [AsitEventOut.model_validate(event) for event in events]


@router.post("/plans/{plan_id}/events", response_model=AsitEventOut)
async def create_my_asit_event(
    plan_id: int,
    payload: AsitEventCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_owned_plan_or_404(plan_id=plan_id, user_id=user.id, db=db)

    event = AsitEvent(
        plan_id=plan_id,
        planned_date=payload.planned_date,
        dose_value=payload.dose_value,
        note=payload.note,
        status="planned",
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)

    return AsitEventOut.model_validate(event)


@router.patch("/events/{event_id}", response_model=AsitEventOut)
async def update_my_asit_event(
    event_id: int,
    payload: AsitEventUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    event = await _get_owned_event_or_404(event_id=event_id, user_id=user.id, db=db)

    if payload.planned_date is not None:
        event.planned_date = payload.planned_date

    if payload.actual_date is not None:
        event.actual_date = payload.actual_date

    if payload.dose_value is not None:
        event.dose_value = payload.dose_value

    if payload.note is not None:
        event.note = payload.note

    if payload.status is not None:
        if payload.status not in ALLOWED_EVENT_STATUSES:
            raise HTTPException(
                status_code=400,
                detail="status must be one of: planned, done, skipped, rescheduled",
            )
        event.status = payload.status

    await db.commit()
    await db.refresh(event)

    return AsitEventOut.model_validate(event)
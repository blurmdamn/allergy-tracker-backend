from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.reminders import Reminder
from app.models.users import User
from app.schemas.reminders import ReminderCreate, ReminderOut, ReminderUpdate

router = APIRouter(prefix="/me/reminders", tags=["Reminders"])

ALLOWED_KINDS = {"asit_visit", "medication", "daily_checkin", "custom"}


async def _get_owned_reminder_or_404(
    reminder_id: int,
    user_id: int,
    db: AsyncSession,
) -> Reminder:
    res = await db.execute(
        select(Reminder).where(
            Reminder.id == reminder_id,
            Reminder.user_id == user_id,
        )
    )
    reminder = res.scalar_one_or_none()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return reminder


@router.get("", response_model=list[ReminderOut])
async def list_my_reminders(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(Reminder)
        .where(Reminder.user_id == user.id)
        .order_by(
            Reminder.is_active.desc(),
            Reminder.scheduled_at.asc().nullslast(),
            Reminder.id.desc(),
        )
    )
    reminders = res.scalars().all()
    return [ReminderOut.model_validate(reminder) for reminder in reminders]


@router.post("", response_model=ReminderOut)
async def create_my_reminder(
    payload: ReminderCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if payload.kind not in ALLOWED_KINDS:
        raise HTTPException(
            status_code=400,
            detail="kind must be one of: asit_visit, medication, daily_checkin, custom",
        )

    reminder = Reminder(
        user_id=user.id,
        kind=payload.kind,
        message=payload.message,
        scheduled_at=payload.scheduled_at,
        active_months=payload.active_months,
        is_active=True,
    )
    db.add(reminder)
    await db.commit()
    await db.refresh(reminder)

    return ReminderOut.model_validate(reminder)


@router.get("/{reminder_id}", response_model=ReminderOut)
async def get_my_reminder(
    reminder_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    reminder = await _get_owned_reminder_or_404(
        reminder_id=reminder_id,
        user_id=user.id,
        db=db,
    )
    return ReminderOut.model_validate(reminder)


@router.patch("/{reminder_id}", response_model=ReminderOut)
async def update_my_reminder(
    reminder_id: int,
    payload: ReminderUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    reminder = await _get_owned_reminder_or_404(
        reminder_id=reminder_id,
        user_id=user.id,
        db=db,
    )

    if payload.kind is not None:
        if payload.kind not in ALLOWED_KINDS:
            raise HTTPException(
                status_code=400,
                detail="kind must be one of: asit_visit, medication, daily_checkin, custom",
            )
        reminder.kind = payload.kind

    if payload.message is not None:
        reminder.message = payload.message

    if payload.scheduled_at is not None:
        reminder.scheduled_at = payload.scheduled_at

    if payload.active_months is not None:
        reminder.active_months = payload.active_months

    if payload.is_active is not None:
        reminder.is_active = payload.is_active

    await db.commit()
    await db.refresh(reminder)

    return ReminderOut.model_validate(reminder)


@router.delete("/{reminder_id}")
async def delete_my_reminder(
    reminder_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    reminder = await _get_owned_reminder_or_404(
        reminder_id=reminder_id,
        user_id=user.id,
        db=db,
    )

    await db.delete(reminder)
    await db.commit()

    return {"message": "Reminder deleted"}
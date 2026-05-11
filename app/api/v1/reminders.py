from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.reminders import Reminder
from app.models.users import User
from app.schemas.reminders import ReminderCreate, ReminderOut, ReminderUpdate

router = APIRouter(prefix="/me/reminders", tags=["Reminders"])

ALLOWED_TYPES = {"asit_visit", "daily_checkin", "questionnaire", "custom"}
ALLOWED_REPEAT_TYPES = {"none", "daily", "weekly", "monthly"}


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


def _validate_type(value: str) -> None:
    if value not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail="type must be one of: asit_visit, daily_checkin, questionnaire, custom",
        )


def _validate_repeat_type(value: str) -> None:
    if value not in ALLOWED_REPEAT_TYPES:
        raise HTTPException(
            status_code=400,
            detail="repeat_type must be one of: none, daily, weekly, monthly",
        )


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
    _validate_type(payload.type)
    _validate_repeat_type(payload.repeat_type)

    reminder = Reminder(
        user_id=user.id,
        type=payload.type,
        repeat_type=payload.repeat_type,
        message=payload.message,
        scheduled_at=payload.scheduled_at,
        active_months=payload.active_months,
        is_active=True,
        sent_at=None,
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

    if payload.type is not None:
        _validate_type(payload.type)
        reminder.type = payload.type

    if payload.repeat_type is not None:
        _validate_repeat_type(payload.repeat_type)
        reminder.repeat_type = payload.repeat_type

    if payload.message is not None:
        reminder.message = payload.message

    if payload.scheduled_at is not None:
        reminder.scheduled_at = payload.scheduled_at

        # Если пользователь перенёс дату, считаем, что это новое ожидание отправки.
        # Для повторяемых sent_at остаётся как "последняя успешная отправка",
        # но для одноразовых после переноса лучше снова разрешить отправку.
        if reminder.repeat_type == "none":
            reminder.sent_at = None

    # Важно: здесь проверяем именно field_set, чтобы можно было очистить active_months = None.
    if "active_months" in payload.model_fields_set:
        reminder.active_months = payload.active_months

    if payload.is_active is not None:
        reminder.is_active = payload.is_active

        # Если пользователь снова включает одноразовое напоминание,
        # разрешаем ему отправиться повторно в указанное scheduled_at.
        if payload.is_active and reminder.repeat_type == "none":
            reminder.sent_at = None

    if payload.sent_at is not None:
        reminder.sent_at = payload.sent_at

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
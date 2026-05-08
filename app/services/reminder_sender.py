from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reminders import Reminder
from app.models.telegram import TelegramAccount
from app.services.telegram_service import reminder_keyboard, send_telegram_message


def get_reminder_type_label(reminder_type: str) -> str:
    labels = {
        "daily_checkin": "Дневник симптомов",
        "asit_visit": "АСИТ",
        "questionnaire": "Контрольный опрос",
        "custom": "Напоминание",
    }

    return labels.get(reminder_type, "Напоминание")


def get_reminder_icon(reminder_type: str) -> str:
    icons = {
        "daily_checkin": "📝",
        "asit_visit": "💉",
        "questionnaire": "📋",
        "custom": "🔔",
    }

    return icons.get(reminder_type, "🔔")


def build_reminder_message(reminder: Reminder) -> str:
    title = get_reminder_type_label(reminder.type)
    icon = get_reminder_icon(reminder.type)
    message = reminder.message or "Пора выполнить запланированное действие."

    return (
        f"{icon} Allergy Tracker\n\n"
        f"{title}\n"
        f"{message}\n\n"
        f"Запланировано: {reminder.scheduled_at.strftime('%d.%m.%Y %H:%M')}"
    )


def is_reminder_active_for_month(reminder: Reminder, now: datetime) -> bool:
    if not reminder.active_months:
        return True

    return now.month in reminder.active_months


async def send_due_reminders(db: AsyncSession) -> int:
    now = datetime.utcnow()

    res = await db.execute(
        select(Reminder)
        .where(
            Reminder.is_active.is_(True),
            Reminder.sent_at.is_(None),
            Reminder.scheduled_at <= now,
        )
        .order_by(Reminder.scheduled_at.asc())
    )
    reminders = res.scalars().all()

    sent_count = 0

    for reminder in reminders:
        if not is_reminder_active_for_month(reminder, now):
            continue

        account_res = await db.execute(
            select(TelegramAccount).where(
                TelegramAccount.user_id == reminder.user_id,
                TelegramAccount.chat_id.is_not(None),
                TelegramAccount.is_active.is_(True),
            )
        )
        account = account_res.scalar_one_or_none()

        if not account or not account.chat_id:
            continue

        ok = await send_telegram_message(
            chat_id=account.chat_id,
            text=build_reminder_message(reminder),
            reply_markup=reminder_keyboard(reminder.type),
        )

        if ok:
            reminder.sent_at = now
            sent_count += 1

    if sent_count:
        await db.commit()

    return sent_count
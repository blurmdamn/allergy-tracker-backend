from __future__ import annotations

from datetime import datetime
from secrets import token_urlsafe
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.telegram import TelegramAccount


def is_telegram_configured() -> bool:
    return bool(settings.TELEGRAM_ENABLED and settings.TELEGRAM_BOT_TOKEN)


def get_bot_username() -> str | None:
    if not settings.TELEGRAM_BOT_USERNAME:
        return None

    return settings.TELEGRAM_BOT_USERNAME.removeprefix("@")


def build_telegram_url(link_token: str) -> str | None:
    username = get_bot_username()

    if not username:
        return None

    return f"https://t.me/{username}?start={link_token}"


def is_public_frontend_url() -> bool:
    """
    Telegram не принимает localhost / 127.0.0.1 в URL-кнопках inline keyboard.
    Поэтому кнопки с url добавляем только для публичного https frontend.
    """
    base_url = settings.FRONTEND_BASE_URL.lower().strip()

    local_markers = [
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
    ]

    return base_url.startswith("https://") and not any(
        marker in base_url for marker in local_markers
    )


def build_frontend_url(path: str = "/") -> str | None:
    if not is_public_frontend_url():
        return None

    base_url = settings.FRONTEND_BASE_URL.rstrip("/")
    normalized_path = path if path.startswith("/") else f"/{path}"

    return f"{base_url}{normalized_path}"


def generate_link_token() -> str:
    return token_urlsafe(24)


def build_inline_keyboard(buttons: list[list[dict[str, str]]]) -> dict[str, Any]:
    return {
        "inline_keyboard": buttons,
    }


def main_menu_keyboard() -> dict[str, Any] | None:
    buttons: list[list[dict[str, str]]] = []

    app_url = build_frontend_url("/")

    if app_url:
        buttons.append(
            [
                {
                    "text": "Открыть Allergy Tracker",
                    "url": app_url,
                }
            ]
        )

    buttons.append(
        [
            {
                "text": "Что я буду получать?",
                "callback_data": "help_reminders",
            }
        ]
    )

    buttons.append(
        [
            {
                "text": "Как отключить Telegram?",
                "callback_data": "unlink_info",
            }
        ]
    )

    return build_inline_keyboard(buttons) if buttons else None


def reminder_keyboard(reminder_type: str) -> dict[str, Any] | None:
    if reminder_type == "daily_checkin":
        primary_text = "Открыть дневник"
        primary_url = build_frontend_url("/daily-checkin")
    elif reminder_type == "asit_visit":
        primary_text = "Открыть график АСИТ"
        primary_url = build_frontend_url("/asit")
    elif reminder_type == "questionnaire":
        primary_text = "Открыть мониторинг"
        primary_url = build_frontend_url("/daily-checkin")
    else:
        primary_text = "Открыть приложение"
        primary_url = build_frontend_url("/")

    buttons: list[list[dict[str, str]]] = []

    if primary_url:
        buttons.append(
            [
                {
                    "text": primary_text,
                    "url": primary_url,
                }
            ]
        )

    statistics_url = build_frontend_url("/results")

    if statistics_url:
        buttons.append(
            [
                {
                    "text": "Моя статистика",
                    "url": statistics_url,
                }
            ]
        )

    return build_inline_keyboard(buttons) if buttons else None


async def get_or_create_telegram_account(
    db: AsyncSession,
    user_id: int,
) -> TelegramAccount:
    res = await db.execute(
        select(TelegramAccount).where(TelegramAccount.user_id == user_id)
    )
    account = res.scalar_one_or_none()

    if account:
        return account

    account = TelegramAccount(
        user_id=user_id,
        link_token=generate_link_token(),
        is_active=True,
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)

    return account


async def refresh_telegram_link_token(
    db: AsyncSession,
    user_id: int,
) -> TelegramAccount:
    account = await get_or_create_telegram_account(db=db, user_id=user_id)

    account.link_token = generate_link_token()
    account.chat_id = None
    account.username = None
    account.first_name = None
    account.linked_at = None
    account.is_active = True

    await db.commit()
    await db.refresh(account)

    return account


async def unlink_telegram_account(
    db: AsyncSession,
    user_id: int,
) -> TelegramAccount | None:
    res = await db.execute(
        select(TelegramAccount).where(TelegramAccount.user_id == user_id)
    )
    account = res.scalar_one_or_none()

    if not account:
        return None

    account.chat_id = None
    account.username = None
    account.first_name = None
    account.linked_at = None
    account.is_active = False

    await db.commit()
    await db.refresh(account)

    return account


async def send_telegram_message(
    chat_id: int,
    text: str,
    reply_markup: dict[str, Any] | None = None,
) -> bool:
    if not is_telegram_configured():
        return False

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"

    payload: dict[str, Any] = {
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": True,
    }

    if reply_markup:
        payload["reply_markup"] = reply_markup

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(url, json=payload)

    if response.status_code != 200:
        print(f"[telegram] sendMessage failed: {response.status_code} {response.text}")
        return False

    return True


async def answer_callback_query(
    callback_query_id: str,
    text: str | None = None,
) -> None:
    if not is_telegram_configured():
        return

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/answerCallbackQuery"

    payload: dict[str, Any] = {
        "callback_query_id": callback_query_id,
    }

    if text:
        payload["text"] = text

    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(url, json=payload)


async def send_start_success_message(chat_id: int) -> None:
    await send_telegram_message(
        chat_id=chat_id,
        text=(
            "✅ Telegram успешно подключён к Allergy Tracker.\n\n"
            "Теперь вы сможете получать напоминания:\n"
            "• заполнить дневник симптомов;\n"
            "• принять лекарство;\n"
            "• запланировать визит по АСИТ;\n"
            "• пройти контрольный опрос.\n\n"
            "Настроить напоминания можно на странице «Настройка напоминаний»."
        ),
        reply_markup=main_menu_keyboard(),
    )


async def send_start_failed_message(chat_id: int) -> None:
    await send_telegram_message(
        chat_id=chat_id,
        text=(
            "Не удалось привязать Telegram.\n\n"
            "Откройте страницу «Настройка напоминаний» в Allergy Tracker "
            "и отсканируйте QR-код ещё раз."
        ),
        reply_markup=None,
    )


async def send_help_message(chat_id: int) -> None:
    await send_telegram_message(
        chat_id=chat_id,
        text=(
            "ℹ️ Какие напоминания можно получать?\n\n"
            "1. Дневник симптомов — напоминание заполнить ежедневный мониторинг.\n"
            "2. Лекарства — напоминание о текущем лечении.\n"
            "3. АСИТ — напоминание о следующем визите или инъекции.\n"
            "4. Контрольный опрос — напоминание пройти оценку состояния.\n\n"
            "Каждое напоминание создаётся в веб-приложении Allergy Tracker."
        ),
        reply_markup=main_menu_keyboard(),
    )


async def send_unlink_info_message(chat_id: int) -> None:
    await send_telegram_message(
        chat_id=chat_id,
        text=(
            "Отключить Telegram можно в веб-приложении на странице "
            "«Настройка напоминаний».\n\n"
            "Это сделано для безопасности: отключение выполняется только "
            "из авторизованного аккаунта."
        ),
        reply_markup=main_menu_keyboard(),
    )


async def get_telegram_updates(offset: int | None = None) -> list[dict[str, Any]]:
    if not is_telegram_configured():
        return []

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/getUpdates"

    params: dict[str, Any] = {
        "timeout": 0,
        "allowed_updates": ["message", "callback_query"],
    }

    if offset is not None:
        params["offset"] = offset

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(url, params=params)

    if response.status_code != 200:
        print(f"[telegram] getUpdates failed: {response.status_code} {response.text}")
        return []

    data = response.json()

    if not data.get("ok"):
        return []

    return data.get("result", [])


def extract_start_token(message_text: str | None) -> str | None:
    if not message_text:
        return None

    parts = message_text.strip().split(maxsplit=1)

    if not parts:
        return None

    command = parts[0].split("@", maxsplit=1)[0]

    if command != "/start":
        return None

    if len(parts) < 2:
        return None

    return parts[1].strip() or None


async def process_telegram_start_message(
    db: AsyncSession,
    *,
    chat_id: int,
    token: str,
    username: str | None,
    first_name: str | None,
) -> bool:
    res = await db.execute(
        select(TelegramAccount).where(TelegramAccount.link_token == token)
    )
    account = res.scalar_one_or_none()

    if not account:
        await send_start_failed_message(chat_id)
        return False

    account.chat_id = chat_id
    account.username = username
    account.first_name = first_name
    account.linked_at = datetime.utcnow()
    account.is_active = True

    await db.commit()

    await send_start_success_message(chat_id)

    return True


async def process_callback_query(callback_query: dict[str, Any]) -> None:
    callback_query_id = callback_query.get("id")
    data = callback_query.get("data")

    message = callback_query.get("message") or {}
    chat = message.get("chat") or {}
    chat_id = chat.get("id")

    if callback_query_id:
        await answer_callback_query(callback_query_id)

    if not chat_id:
        return

    if data == "help_reminders":
        await send_help_message(chat_id=int(chat_id))
        return

    if data == "unlink_info":
        await send_unlink_info_message(chat_id=int(chat_id))
        return
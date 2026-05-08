from __future__ import annotations

import asyncio
from contextlib import suppress

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.services.reminder_sender import send_due_reminders
from app.services.telegram_service import (
    extract_start_token,
    get_telegram_updates,
    is_telegram_configured,
    process_callback_query,
    process_telegram_start_message,
)


class BackgroundTasksManager:
    def __init__(self) -> None:
        self._tasks: list[asyncio.Task] = []
        self._telegram_offset: int | None = None

    async def start(self) -> None:
        if not settings.TELEGRAM_ENABLED:
            print("[telegram] disabled")
            return

        if not is_telegram_configured():
            print("[telegram] TELEGRAM_BOT_TOKEN is not configured")
            return

        if settings.TELEGRAM_POLLING_ENABLED:
            self._tasks.append(asyncio.create_task(self._telegram_polling_loop()))
            print("[telegram] polling started")

        self._tasks.append(asyncio.create_task(self._reminder_loop()))
        print("[reminders] sender loop started")

    async def stop(self) -> None:
        for task in self._tasks:
            task.cancel()

        for task in self._tasks:
            with suppress(asyncio.CancelledError):
                await task

        self._tasks.clear()

    async def _telegram_polling_loop(self) -> None:
        while True:
            try:
                updates = await get_telegram_updates(offset=self._telegram_offset)

                for update in updates:
                    update_id = update.get("update_id")

                    if update_id is not None:
                        self._telegram_offset = int(update_id) + 1

                    callback_query = update.get("callback_query")
                    if callback_query:
                        await process_callback_query(callback_query)
                        continue

                    message = update.get("message") or {}
                    text = message.get("text")
                    token = extract_start_token(text)

                    if not token:
                        continue

                    chat = message.get("chat") or {}
                    from_user = message.get("from") or {}

                    chat_id = chat.get("id")

                    if not chat_id:
                        continue

                    async with AsyncSessionLocal() as db:
                        await process_telegram_start_message(
                            db,
                            chat_id=int(chat_id),
                            token=token,
                            username=from_user.get("username"),
                            first_name=from_user.get("first_name"),
                        )

            except Exception as exc:
                print(f"[telegram] polling error: {exc}")

            await asyncio.sleep(settings.TELEGRAM_POLLING_INTERVAL_SECONDS)

    async def _reminder_loop(self) -> None:
        while True:
            try:
                async with AsyncSessionLocal() as db:
                    sent_count = await send_due_reminders(db)

                if sent_count:
                    print(f"[reminders] sent: {sent_count}")

            except Exception as exc:
                print(f"[reminders] sender error: {exc}")

            await asyncio.sleep(settings.TELEGRAM_REMINDER_INTERVAL_SECONDS)


background_tasks = BackgroundTasksManager()
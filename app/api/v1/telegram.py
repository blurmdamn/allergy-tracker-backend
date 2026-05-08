from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.core.config import settings
from app.models.users import User
from app.schemas.telegram import TelegramLinkOut, TelegramStatusOut
from app.services.telegram_service import (
    build_telegram_url,
    get_or_create_telegram_account,
    refresh_telegram_link_token,
    unlink_telegram_account,
)

router = APIRouter(prefix="/me/telegram", tags=["Telegram"])


@router.get("/status", response_model=TelegramStatusOut)
async def get_my_telegram_status(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    account = await get_or_create_telegram_account(db=db, user_id=user.id)

    return TelegramStatusOut(
        is_linked=bool(account.chat_id and account.is_active),
        bot_username=settings.TELEGRAM_BOT_USERNAME,
        bot_url=build_telegram_url(account.link_token),
        chat_id=account.chat_id,
        username=account.username,
        linked_at=account.linked_at,
    )


@router.get("/link", response_model=TelegramLinkOut)
async def get_my_telegram_link(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    account = await get_or_create_telegram_account(db=db, user_id=user.id)

    return TelegramLinkOut(
        bot_username=settings.TELEGRAM_BOT_USERNAME,
        link_token=account.link_token,
        bot_url=build_telegram_url(account.link_token),
        is_linked=bool(account.chat_id and account.is_active),
        chat_id=account.chat_id,
        username=account.username,
    )


@router.post("/refresh-link", response_model=TelegramLinkOut)
async def refresh_my_telegram_link(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    account = await refresh_telegram_link_token(db=db, user_id=user.id)

    return TelegramLinkOut(
        bot_username=settings.TELEGRAM_BOT_USERNAME,
        link_token=account.link_token,
        bot_url=build_telegram_url(account.link_token),
        is_linked=False,
        chat_id=account.chat_id,
        username=account.username,
    )


@router.delete("/unlink")
async def unlink_my_telegram(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await unlink_telegram_account(db=db, user_id=user.id)

    return {"message": "Telegram disconnected"}
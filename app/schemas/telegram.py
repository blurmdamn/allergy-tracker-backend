from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TelegramLinkOut(BaseModel):
    bot_username: str | None = None
    link_token: str
    bot_url: str | None = None
    is_linked: bool
    chat_id: int | None = None
    username: str | None = None


class TelegramStatusOut(BaseModel):
    is_linked: bool
    bot_username: str | None = None
    bot_url: str | None = None
    chat_id: int | None = None
    username: str | None = None
    linked_at: datetime | None = None


class TelegramAccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    chat_id: int | None = None
    username: str | None = None
    first_name: str | None = None
    link_token: str
    is_active: bool
    linked_at: datetime | None = None
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReminderCreate(BaseModel):
    type: str
    repeat_type: str = "none"
    message: str = Field(min_length=1, max_length=512)
    scheduled_at: datetime
    active_months: list[int] | None = None


class ReminderUpdate(BaseModel):
    type: str | None = None
    repeat_type: str | None = None
    message: str | None = Field(default=None, min_length=1, max_length=512)
    scheduled_at: datetime | None = None
    active_months: list[int] | None = None
    is_active: bool | None = None
    sent_at: datetime | None = None


class ReminderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    type: str
    repeat_type: str
    message: str
    scheduled_at: datetime
    active_months: list[int] | None = None
    is_active: bool
    sent_at: datetime | None = None
    created_at: datetime
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ReminderCreate(BaseModel):
    type: str  # asit_visit / daily_checkin / questionnaire / custom
    message: str | None = None
    scheduled_at: datetime
    active_months: list[int] | None = None  # 1..12


class ReminderUpdate(BaseModel):
    type: str | None = None
    message: str | None = None
    scheduled_at: datetime | None = None
    active_months: list[int] | None = None
    is_active: bool | None = None


class ReminderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    message: str | None = None
    scheduled_at: datetime
    active_months: list[int] | None = None
    is_active: bool
    sent_at: datetime | None = None
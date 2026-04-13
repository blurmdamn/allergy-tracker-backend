from datetime import datetime

from pydantic import BaseModel


class ReminderCreate(BaseModel):
    type: str  # asit_visit / daily_checkin / questionnaire / custom
    message: str | None = None
    scheduled_at: datetime
    active_months: list[int] | None = None  # 1..12


class ReminderOut(BaseModel):
    id: int
    type: str
    message: str | None
    scheduled_at: datetime
    active_months: list[int] | None
    is_active: bool
    sent_at: datetime | None

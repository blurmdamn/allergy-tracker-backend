from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ReminderCreate(BaseModel):
    kind: str = Field(description="asit_visit | medication | daily_checkin | custom")
    message: str
    scheduled_at: datetime | None = None
    active_months: list[int] | None = None


    @field_validator("active_months")
    @classmethod
    def validate_active_months(cls, v: list[int] | None):
        if v is None:
            return v
        for month in v:
            if month < 1 or month > 12:
                raise ValueError("active_months values must be between 1 and 12")
        return v


class ReminderUpdate(BaseModel):
    kind: str | None = None
    message: str | None = None
    scheduled_at: datetime | None = None
    active_months: list[int] | None = None
    is_active: bool | None = None


    @field_validator("active_months")
    @classmethod
    def validate_active_months(cls, v: list[int] | None):
        if v is None:
            return v
        for month in v:
            if month < 1 or month > 12:
                raise ValueError("active_months values must be between 1 and 12")
        return v


class ReminderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    kind: str
    message: str
    scheduled_at: datetime | None = None
    active_months: list[int] | None = None
    is_active: bool
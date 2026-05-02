from datetime import date

from pydantic import BaseModel


class DashboardTodayCheckinOut(BaseModel):
    date: date
    filled: bool
    severity_level: str | None = None
    nasal_score: int | None = None
    ocular_score: int | None = None
    symptom_total_score: int | None = None
    medication_score: int | None = None
    day_total_score: int | None = None


class DashboardNextAsitEventOut(BaseModel):
    id: int
    plan_id: int
    planned_date: date
    actual_date: date | None = None
    status: str
    dose_value: str | None = None
    note: str | None = None


class DashboardOut(BaseModel):
    today_checkin: DashboardTodayCheckinOut
    active_medications_count: int
    next_asit_event: DashboardNextAsitEventOut | None = None
    severe_days_last_7: int
    streak: int
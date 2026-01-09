from datetime import date
from pydantic import BaseModel

class AsitPlanCreate(BaseModel):
    regimen: str  # conventional / daily / accelerated
    target_allergen_code: str | None = None
    medication_code: str | None = None
    interval_days: int | None = None
    dose_unit: str | None = None
    started_at: date | None = None

class AsitPlanOut(BaseModel):
    id: int
    regimen: str
    interval_days: int | None
    dose_unit: str | None
    started_at: date | None
    is_active: bool


class AsitEventCreate(BaseModel):
    planned_date: date
    dose_value: str | None = None
    note: str | None = None

class AsitEventOut(BaseModel):
    id: int
    planned_date: date
    actual_date: date | None
    dose_value: str | None
    status: str  # planned / done / skipped / rescheduled
    note: str | None

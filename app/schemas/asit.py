from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class AsitPlanCreate(BaseModel):
    regimen: str = Field(description="conventional | daily | accelerated")
    target_allergen_code: str | None = None
    medication_code: str | None = None
    interval_days: int | None = None
    dose_unit: str | None = None
    started_at: date | None = None


class AsitPlanUpdate(BaseModel):
    regimen: str | None = None
    target_allergen_code: str | None = None
    medication_code: str | None = None
    interval_days: int | None = None
    dose_unit: str | None = None
    started_at: date | None = None
    is_active: bool | None = None


class AsitPlanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    regimen: str
    target_allergen_code: str | None = None
    medication_code: str | None = None
    interval_days: int | None = None
    dose_unit: str | None = None
    started_at: date | None = None
    is_active: bool


class AsitEventCreate(BaseModel):
    planned_date: date
    dose_value: str | None = None
    note: str | None = None


class AsitEventUpdate(BaseModel):
    planned_date: date | None = None
    actual_date: date | None = None
    dose_value: str | None = None
    status: str | None = None
    note: str | None = None


class AsitEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    planned_date: date
    actual_date: date | None = None
    dose_value: str | None = None
    status: str
    note: str | None = None
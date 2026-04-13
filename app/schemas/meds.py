from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class PatientMedicationCreate(BaseModel):
    medication_code: str
    dose_text: str | None = None
    times_per_day: int | None = Field(default=None, ge=1)
    interval_hours: int | None = Field(default=None, ge=1)
    started_at: date | None = None
    ended_at: date | None = None


class PatientMedicationUpdate(BaseModel):
    medication_code: str | None = None
    dose_text: str | None = None
    times_per_day: int | None = Field(default=None, ge=1)
    interval_hours: int | None = Field(default=None, ge=1)
    started_at: date | None = None
    ended_at: date | None = None
    is_active: bool | None = None


class PatientMedicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    medication_code: str
    dose_text: str | None = None
    times_per_day: int | None = None
    interval_hours: int | None = None
    started_at: date | None = None
    ended_at: date | None = None
    is_active: bool


class MedicationIntakeLogCreate(BaseModel):
    intake_date: date
    tablets_per_day: int | None = Field(default=None, ge=1)
    effect: str | None = None
    note: str | None = None


class MedicationIntakeLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    intake_date: date
    tablets_per_day: int | None = None
    effect: str | None = None
    note: str | None = None
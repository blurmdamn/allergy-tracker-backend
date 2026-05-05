from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


TreatmentEffect = Literal["good", "partial", "none"]


class PatientMedicationCreate(BaseModel):
    medication_code: str
    started_at: date | None = None
    ended_at: date | None = None
    dose_text: str | None = None
    times_per_day: int | None = Field(default=None, ge=0)
    interval_hours: int | None = Field(default=None, ge=0)
    treatment_effect: TreatmentEffect | None = None


class PatientMedicationUpdate(BaseModel):
    medication_code: str | None = None
    started_at: date | None = None
    ended_at: date | None = None
    dose_text: str | None = None
    times_per_day: int | None = Field(default=None, ge=0)
    interval_hours: int | None = Field(default=None, ge=0)
    treatment_effect: TreatmentEffect | None = None
    is_active: bool | None = None


class PatientMedicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    medication_code: str | None = None
    is_active: bool
    started_at: date | None = None
    ended_at: date | None = None
    dose_text: str | None = None
    times_per_day: int | None = None
    interval_hours: int | None = None
    treatment_effect: str | None = None


class MedicationIntakeLogCreate(BaseModel):
    intake_date: datetime | None = None
    dose_taken: int | None = Field(default=None, ge=0)
    effect: TreatmentEffect | None = None
    note: str | None = None


class MedicationIntakeLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_medication_id: int
    logged_at: datetime
    dose_taken: int | None = None
    effect: str | None = None
    note: str | None = None
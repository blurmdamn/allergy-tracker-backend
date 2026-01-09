from datetime import date, datetime
from pydantic import BaseModel

class PatientMedicationCreate(BaseModel):
    medication_code: str
    started_at: date | None = None
    dose_text: str | None = None
    times_per_day: int | None = None
    interval_hours: int | None = None

class PatientMedicationOut(BaseModel):
    id: int
    medication_code: str
    is_active: bool
    started_at: date | None
    ended_at: date | None
    dose_text: str | None
    times_per_day: int | None
    interval_hours: int | None


class MedicationIntakeLogCreate(BaseModel):
    tablets_per_day: int | None = None
    effect: str | None = None  # success / partial / fail
    note: str | None = None

class MedicationIntakeLogOut(MedicationIntakeLogCreate):
    id: int
    logged_at: datetime

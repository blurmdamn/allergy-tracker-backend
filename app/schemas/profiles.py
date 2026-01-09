from datetime import date
from pydantic import BaseModel

class PatientProfileOut(BaseModel):
    full_name: str | None
    birth_date: date | None
    sex: str | None  # female / male / other

class PatientProfileUpdate(BaseModel):
    full_name: str | None = None
    birth_date: date | None = None
    sex: str | None = None

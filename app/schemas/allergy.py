from datetime import date
from pydantic import BaseModel, Field

class AllergyOut(BaseModel):
    symptoms_start_date: date | None

    # месяцы 1..12 (мультивыбор)
    active_months: list[int] = Field(default_factory=list)

    # contact_only / daily
    frequency: str | None

    # выбранные элементы из справочников
    allergen_codes: list[str] = Field(default_factory=list)
    symptom_codes: list[str] = Field(default_factory=list)

class AllergyUpdate(BaseModel):
    symptoms_start_date: date | None = None
    active_months: list[int] | None = None
    frequency: str | None = None
    allergen_codes: list[str] | None = None
    symptom_codes: list[str] | None = None

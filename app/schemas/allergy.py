from datetime import date

from pydantic import BaseModel, Field


class AllergyOut(BaseModel):
    symptoms_start_date: date | None
    active_months: list[int] = Field(default_factory=list)
    frequency: str | None
    allergen_codes: list[str] = Field(default_factory=list)
    symptom_codes: list[str] = Field(default_factory=list)


class AllergyUpdate(BaseModel):
    symptoms_start_date: date | None = None
    active_months: list[int] | None = None
    frequency: str | None = None
    allergen_codes: list[str] | None = None
    symptom_codes: list[str] | None = None

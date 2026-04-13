from datetime import date

from pydantic import BaseModel


class ProfileOut(BaseModel):
    full_name: str | None
    birth_date: date | None
    sex: str | None  # female / male / other


class ProfileUpdate(BaseModel):
    full_name: str | None = None
    birth_date: date | None = None
    sex: str | None = None

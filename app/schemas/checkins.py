from datetime import date
from pydantic import BaseModel, Field

class DailyCheckinUpsert(BaseModel):
    date: date

    # оценки симптомов 0–3
    symptom_scores: dict[str, int] = Field(default_factory=dict)

    # общая оценка (по желанию врача)
    overall_score: int | None = None

    note: str | None = None

class DailyCheckinOut(DailyCheckinUpsert):
    pass

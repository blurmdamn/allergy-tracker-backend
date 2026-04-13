from datetime import date
from pydantic import BaseModel, ConfigDict, Field


class CheckinQuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    text: str
    domain: str
    answer_type: str
    sort_order: int
    is_active: bool


class DailyCheckinAnswerIn(BaseModel):
    question_code: str
    score_value: int | None = Field(default=None, ge=0, le=3)
    bool_value: bool | None = None
    text_value: str | None = None
    choice_value: str | None = None
    choice_values_json: str | None = None


class DailyMedicationUsageIn(BaseModel):
    patient_medication_id: int
    times_taken: int | None = Field(default=None, ge=0)
    effect: str | None = None
    note: str | None = None


class DailyMedicationUsageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_medication_id: int
    times_taken: int | None = None
    effect: str | None = None
    note: str | None = None


class DailyCheckinUpsert(BaseModel):
    answers: list[DailyCheckinAnswerIn] = Field(default_factory=list)
    medication_usage: list[DailyMedicationUsageIn] = Field(default_factory=list)


class DailyCheckinAnswerOut(BaseModel):
    question_code: str
    domain: str
    answer_type: str
    score_value: int | None = None
    bool_value: bool | None = None
    text_value: str | None = None
    choice_value: str | None = None
    choice_values_json: str | None = None


class DailyCheckinOut(BaseModel):
    id: int
    checkin_date: date

    nasal_score: int
    ocular_score: int
    symptom_total_score: int
    medication_score: int
    day_total_score: int
    severity_level: str

    wellbeing_score: int | None = None
    activity_impact_score: int | None = None
    sleep_impact_score: int | None = None

    had_allergen_contact: bool | None = None
    trigger_note: str | None = None
    note: str | None = None

    answers: list[DailyCheckinAnswerOut]
    medication_usage: list[DailyMedicationUsageOut]


class CalendarDayOut(BaseModel):
    date: date
    symptom_total_score: int
    medication_score: int
    day_total_score: int
    severity_level: str


class CalendarMonthOut(BaseModel):
    year: int
    month: int
    days: list[CalendarDayOut]
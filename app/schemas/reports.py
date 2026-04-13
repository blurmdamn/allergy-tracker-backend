from datetime import date
from pydantic import BaseModel


class ReportProfileOut(BaseModel):
    full_name: str | None = None
    birth_date: date | None = None
    sex: str | None = None


class ReportAllergyOut(BaseModel):
    symptoms_start_date: date | None = None
    active_months: list[int] | None = None
    frequency: str | None = None
    allergens: list[str]
    symptoms: list[str]


class ReportMedicationCourseOut(BaseModel):
    id: int
    medication_code: str
    medication_name: str
    form: str
    started_at: date | None = None
    ended_at: date | None = None
    is_active: bool
    dose_text: str | None = None
    times_per_day: int | None = None
    interval_hours: int | None = None


class ReportMedicationLogOut(BaseModel):
    id: int
    patient_medication_id: int
    logged_at: str
    tablets_per_day: int | None = None
    effect: str | None = None
    note: str | None = None


class ReportAsitPlanOut(BaseModel):
    id: int
    regimen: str
    target_allergen_code: str | None = None
    target_allergen_name: str | None = None
    medication_code: str | None = None
    medication_name: str | None = None
    interval_days: int | None = None
    dose_unit: str | None = None
    started_at: date | None = None
    is_active: bool


class ReportAsitEventOut(BaseModel):
    id: int
    plan_id: int
    planned_date: date
    actual_date: date | None = None
    dose_value: str | None = None
    status: str
    note: str | None = None


class ReportCheckinDayOut(BaseModel):
    date: date
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


class ReportStatsOut(BaseModel):
    days_in_period: int
    filled_checkins_count: int
    average_nasal_score: float
    average_ocular_score: float
    average_symptom_total_score: float
    average_day_total_score: float
    max_symptom_total_score: int
    max_day_total_score: int
    severe_days_count: int
    active_medication_courses_count: int
    asit_events_total: int
    asit_events_done: int
    asit_events_skipped: int
    asit_events_rescheduled: int


class ReportSummaryOut(BaseModel):
    date_from: date
    date_to: date
    profile: ReportProfileOut
    allergy: ReportAllergyOut
    active_medications: list[ReportMedicationCourseOut]
    medication_logs: list[ReportMedicationLogOut]
    asit_plans: list[ReportAsitPlanOut]
    asit_events: list[ReportAsitEventOut]
    checkins: list[ReportCheckinDayOut]
    stats: ReportStatsOut
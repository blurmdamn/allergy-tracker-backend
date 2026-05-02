from __future__ import annotations

from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.allergy import PatientAllergy, patient_allergen, patient_symptom
from app.models.asit import AsitEvent, AsitPlan
from app.models.checkins import DailyCheckin
from app.models.dicts import Allergen, Medication, Symptom
from app.models.meds import MedicationIntakeLog, PatientMedication
from app.models.profiles import PatientProfile
from app.models.users import User
from app.schemas.reports import (
    ReportAllergyOut,
    ReportAsitEventOut,
    ReportAsitPlanOut,
    ReportCheckinDayOut,
    ReportMedicationCourseOut,
    ReportMedicationLogOut,
    ReportProfileOut,
    ReportStatsOut,
    ReportSummaryOut,
)

router = APIRouter(prefix="/me/report", tags=["Reports"])


def _round2(value: float | None) -> float:
    if value is None:
        return 0.0
    return round(float(value), 2)


@router.get("/summary", response_model=ReportSummaryOut)
async def get_my_report_summary(
    date_from: date = Query(...),
    date_to: date = Query(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if date_to < date_from:
        raise HTTPException(status_code=400, detail="date_to cannot be earlier than date_from")

    # -------------------------
    # Profile
    # -------------------------
    profile_res = await db.execute(
        select(PatientProfile).where(PatientProfile.user_id == user.id)
    )
    profile = profile_res.scalar_one_or_none()

    profile_out = ReportProfileOut(
        full_name=profile.full_name if profile else None,
        birth_date=profile.birth_date if profile else None,
        sex=profile.sex if profile else None,
    )

    # -------------------------
    # Allergy block
    # -------------------------
    allergy_res = await db.execute(
        select(PatientAllergy).where(PatientAllergy.user_id == user.id)
    )
    allergy = allergy_res.scalar_one_or_none()

    allergens_res = await db.execute(
        select(Allergen.name)
        .select_from(patient_allergen.join(Allergen, patient_allergen.c.allergen_id == Allergen.id))
        .where(patient_allergen.c.user_id == user.id)
        .order_by(Allergen.name.asc())
    )
    allergen_names = list(allergens_res.scalars().all())

    symptoms_res = await db.execute(
        select(Symptom.name)
        .select_from(patient_symptom.join(Symptom, patient_symptom.c.symptom_id == Symptom.id))
        .where(patient_symptom.c.user_id == user.id)
        .order_by(Symptom.name.asc())
    )
    symptom_names = list(symptoms_res.scalars().all())

    allergy_out = ReportAllergyOut(
        symptoms_start_date=allergy.symptoms_start_date if allergy else None,
        active_months=allergy.active_months if allergy else None,
        frequency=allergy.frequency if allergy else None,
        allergens=allergen_names,
        symptoms=symptom_names,
    )

    # -------------------------
    # Active medication courses
    # -------------------------
    med_courses_res = await db.execute(
        select(PatientMedication, Medication)
        .join(Medication, Medication.id == PatientMedication.medication_id)
        .where(PatientMedication.user_id == user.id)
        .order_by(
            PatientMedication.is_active.desc(),
            PatientMedication.started_at.desc(),
            PatientMedication.id.desc(),
        )
    )
    med_courses_rows = med_courses_res.all()

    active_medications = [
        ReportMedicationCourseOut(
            id=course.id,
            medication_code=med.code,
            medication_name=med.name,
            form=med.form,
            started_at=course.started_at,
            ended_at=course.ended_at,
            is_active=course.is_active,
            dose_text=course.dose_text,
            times_per_day=course.times_per_day,
            interval_hours=course.interval_hours,
        )
        for course, med in med_courses_rows
        if course.is_active
    ]

    user_course_ids = [course.id for course, _ in med_courses_rows]

    # -------------------------
    # Medication logs in period
    # -------------------------
    medication_logs: list[ReportMedicationLogOut] = []
    if user_course_ids:
        dt_from = datetime.combine(date_from, datetime.min.time())
        dt_to = datetime.combine(date_to, datetime.max.time())

        logs_res = await db.execute(
            select(MedicationIntakeLog)
            .where(
                MedicationIntakeLog.patient_medication_id.in_(user_course_ids),
                MedicationIntakeLog.logged_at >= dt_from,
                MedicationIntakeLog.logged_at <= dt_to,
            )
            .order_by(MedicationIntakeLog.logged_at.desc(), MedicationIntakeLog.id.desc())
        )
        logs = logs_res.scalars().all()

        medication_logs = [
            ReportMedicationLogOut(
                id=log.id,
                patient_medication_id=log.patient_medication_id,
                logged_at=log.logged_at,
                dose_taken=log.dose_taken,
                effect=log.effect,
                note=log.note,
            )
            for log in logs
        ]

    # -------------------------
    # ASIT plans
    # -------------------------
    asit_plans_res = await db.execute(
        select(
            AsitPlan,
            Allergen.code,
            Allergen.name,
            Medication.code,
            Medication.name,
        )
        .outerjoin(Allergen, Allergen.id == AsitPlan.target_allergen_id)
        .outerjoin(Medication, Medication.id == AsitPlan.medication_id)
        .where(AsitPlan.user_id == user.id)
        .order_by(AsitPlan.is_active.desc(), AsitPlan.created_at.desc(), AsitPlan.id.desc())
    )
    asit_plan_rows = asit_plans_res.all()

    asit_plans = [
        ReportAsitPlanOut(
            id=plan.id,
            regimen=plan.regimen,
            target_allergen_code=allergen_code,
            target_allergen_name=allergen_name,
            medication_code=med_code,
            medication_name=med_name,
            interval_days=plan.interval_days,
            dose_unit=plan.dose_unit,
            started_at=plan.started_at,
            is_active=plan.is_active,
        )
        for plan, allergen_code, allergen_name, med_code, med_name in asit_plan_rows
    ]

    plan_ids = [plan.id for plan, *_ in asit_plan_rows]

    # -------------------------
    # ASIT events in period
    # -------------------------
    asit_events: list[ReportAsitEventOut] = []
    if plan_ids:
        events_res = await db.execute(
            select(AsitEvent)
            .where(
                AsitEvent.plan_id.in_(plan_ids),
                AsitEvent.planned_date >= date_from,
                AsitEvent.planned_date <= date_to,
            )
            .order_by(AsitEvent.planned_date.asc(), AsitEvent.id.asc())
        )
        events = events_res.scalars().all()

        asit_events = [
            ReportAsitEventOut(
                id=event.id,
                plan_id=event.plan_id,
                planned_date=event.planned_date,
                actual_date=event.actual_date,
                dose_value=event.dose_value,
                status=event.status,
                note=event.note,
            )
            for event in events
        ]

    # -------------------------
    # Check-ins in period
    # -------------------------
    checkins_res = await db.execute(
        select(DailyCheckin)
        .where(
            DailyCheckin.user_id == user.id,
            DailyCheckin.checkin_date >= date_from,
            DailyCheckin.checkin_date <= date_to,
        )
        .order_by(DailyCheckin.checkin_date.asc(), DailyCheckin.id.asc())
    )
    checkin_rows = checkins_res.scalars().all()

    checkins = [
        ReportCheckinDayOut(
            date=row.checkin_date,
            nasal_score=row.nasal_score,
            ocular_score=row.ocular_score,
            symptom_total_score=row.symptom_total_score,
            medication_score=row.medication_score,
            day_total_score=row.day_total_score,
            severity_level=row.severity_level,
            wellbeing_score=row.wellbeing_score,
            activity_impact_score=row.activity_impact_score,
            sleep_impact_score=row.sleep_impact_score,
            had_allergen_contact=row.had_allergen_contact,
            trigger_note=row.trigger_note,
            note=row.note,
        )
        for row in checkin_rows
    ]

    # -------------------------
    # Stats
    # -------------------------
    days_in_period = (date_to - date_from).days + 1
    filled_checkins_count = len(checkin_rows)

    avg_nasal = _round2(
        sum(item.nasal_score for item in checkin_rows) / filled_checkins_count
        if filled_checkins_count else 0
    )
    avg_ocular = _round2(
        sum(item.ocular_score for item in checkin_rows) / filled_checkins_count
        if filled_checkins_count else 0
    )
    avg_symptom_total = _round2(
        sum(item.symptom_total_score for item in checkin_rows) / filled_checkins_count
        if filled_checkins_count else 0
    )
    avg_day_total = _round2(
        sum(item.day_total_score for item in checkin_rows) / filled_checkins_count
        if filled_checkins_count else 0
    )

    max_symptom_total = max((item.symptom_total_score for item in checkin_rows), default=0)
    max_day_total = max((item.day_total_score for item in checkin_rows), default=0)
    severe_days_count = sum(1 for item in checkin_rows if item.severity_level == "severe")

    asit_events_total = len(asit_events)
    asit_events_done = sum(1 for e in asit_events if e.status == "done")
    asit_events_skipped = sum(1 for e in asit_events if e.status == "skipped")
    asit_events_rescheduled = sum(1 for e in asit_events if e.status == "rescheduled")

    stats = ReportStatsOut(
        days_in_period=days_in_period,
        filled_checkins_count=filled_checkins_count,
        average_nasal_score=avg_nasal,
        average_ocular_score=avg_ocular,
        average_symptom_total_score=avg_symptom_total,
        average_day_total_score=avg_day_total,
        max_symptom_total_score=max_symptom_total,
        max_day_total_score=max_day_total,
        severe_days_count=severe_days_count,
        active_medication_courses_count=len(active_medications),
        asit_events_total=asit_events_total,
        asit_events_done=asit_events_done,
        asit_events_skipped=asit_events_skipped,
        asit_events_rescheduled=asit_events_rescheduled,
    )

    return ReportSummaryOut(
        date_from=date_from,
        date_to=date_to,
        profile=profile_out,
        allergy=allergy_out,
        active_medications=active_medications,
        medication_logs=medication_logs,
        asit_plans=asit_plans,
        asit_events=asit_events,
        checkins=checkins,
        stats=stats,
    )
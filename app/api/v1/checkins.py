from __future__ import annotations

from datetime import date
import calendar

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import delete, extract, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.checkins import (
    CheckinQuestion,
    DailyCheckin,
    DailyCheckinAnswer,
    DailyMedicationUsage,
)
from app.models.meds import PatientMedication
from app.models.users import User
from app.schemas.checkins import (
    CalendarDayOut,
    CalendarMonthOut,
    CheckinQuestionOut,
    DailyCheckinAnswerOut,
    DailyCheckinOut,
    DailyCheckinUpsert,
    DailyMedicationUsageOut,
)

router = APIRouter(prefix="/me/checkins", tags=["Checkins"])

NASAL_CODES = {
    "runny_nose",
    "nasal_congestion",
    "sneezing",
    "itchy_nose",
}

OCULAR_CODES = {
    "red_eyes",
    "watery_eyes",
    "itchy_eyes",
}

ALLOWED_MED_EFFECTS = {"good", "partial", "none"}


def get_severity_level(symptom_total_score: int) -> str:
    if symptom_total_score == 0:
        return "none"
    if symptom_total_score <= 5:
        return "mild"
    if symptom_total_score <= 10:
        return "moderate"
    if symptom_total_score <= 15:
        return "high"
    return "severe"


def calculate_medication_score(usages_count: int) -> int:
    if usages_count <= 0:
        return 0
    if usages_count == 1:
        return 1
    if usages_count >= 2:
        return 2
    return 0


async def _get_questions_map(db: AsyncSession) -> dict[str, CheckinQuestion]:
    res = await db.execute(
        select(CheckinQuestion)
        .where(CheckinQuestion.is_active.is_(True))
        .order_by(CheckinQuestion.sort_order.asc(), CheckinQuestion.id.asc())
    )
    questions = res.scalars().all()
    return {q.code: q for q in questions}


async def _get_owned_checkin(
    user_id: int,
    checkin_date: date,
    db: AsyncSession,
) -> DailyCheckin | None:
    res = await db.execute(
        select(DailyCheckin).where(
            DailyCheckin.user_id == user_id,
            DailyCheckin.checkin_date == checkin_date,
        )
    )
    return res.scalar_one_or_none()


async def _get_owned_patient_medications_map(
    user_id: int,
    db: AsyncSession,
) -> dict[int, PatientMedication]:
    res = await db.execute(
        select(PatientMedication).where(PatientMedication.user_id == user_id)
    )
    meds = res.scalars().all()
    return {m.id: m for m in meds}


async def _serialize_checkin(
    checkin: DailyCheckin,
    db: AsyncSession,
) -> DailyCheckinOut:
    answers_res = await db.execute(
        select(
            DailyCheckinAnswer,
            CheckinQuestion.code,
            CheckinQuestion.domain,
            CheckinQuestion.answer_type,
        )
        .join(CheckinQuestion, CheckinQuestion.id == DailyCheckinAnswer.question_id)
        .where(DailyCheckinAnswer.checkin_id == checkin.id)
        .order_by(CheckinQuestion.sort_order.asc(), CheckinQuestion.id.asc())
    )
    answers_rows = answers_res.all()

    med_res = await db.execute(
        select(DailyMedicationUsage)
        .where(DailyMedicationUsage.checkin_id == checkin.id)
        .order_by(DailyMedicationUsage.id.asc())
    )
    medication_usage = med_res.scalars().all()

    return DailyCheckinOut(
        id=checkin.id,
        checkin_date=checkin.checkin_date,
        nasal_score=checkin.nasal_score,
        ocular_score=checkin.ocular_score,
        symptom_total_score=checkin.symptom_total_score,
        medication_score=checkin.medication_score,
        day_total_score=checkin.day_total_score,
        severity_level=checkin.severity_level,
        wellbeing_score=checkin.wellbeing_score,
        activity_impact_score=checkin.activity_impact_score,
        sleep_impact_score=checkin.sleep_impact_score,
        had_allergen_contact=checkin.had_allergen_contact,
        trigger_note=checkin.trigger_note,
        note=checkin.note,
        answers=[
            DailyCheckinAnswerOut(
                question_code=code,
                domain=domain,
                answer_type=answer_type,
                score_value=answer.score_value,
                bool_value=answer.bool_value,
                text_value=answer.text_value,
                choice_value=answer.choice_value,
                choice_values_json=answer.choice_values_json,
            )
            for answer, code, domain, answer_type in answers_rows
        ],
        medication_usage=[
            DailyMedicationUsageOut.model_validate(item)
            for item in medication_usage
        ],
    )


@router.get("/questions", response_model=list[CheckinQuestionOut])
async def list_checkin_questions(db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(CheckinQuestion)
        .where(CheckinQuestion.is_active.is_(True))
        .order_by(CheckinQuestion.sort_order.asc(), CheckinQuestion.id.asc())
    )
    return [CheckinQuestionOut.model_validate(q) for q in res.scalars().all()]


@router.get("/{checkin_date}", response_model=DailyCheckinOut)
async def get_my_checkin_by_date(
    checkin_date: date,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    checkin = await _get_owned_checkin(user.id, checkin_date, db)
    if not checkin:
        raise HTTPException(status_code=404, detail="Check-in not found")
    return await _serialize_checkin(checkin, db)


@router.put("/{checkin_date}", response_model=DailyCheckinOut)
async def upsert_my_checkin(
    checkin_date: date,
    payload: DailyCheckinUpsert,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    questions_map = await _get_questions_map(db)
    owned_medications_map = await _get_owned_patient_medications_map(user.id, db)

    # validate answers
    seen_question_codes: set[str] = set()
    nasal_score = 0
    ocular_score = 0

    wellbeing_score: int | None = None
    activity_impact_score: int | None = None
    sleep_impact_score: int | None = None
    had_allergen_contact: bool | None = None
    trigger_note: str | None = None
    note: str | None = None

    normalized_answers: list[tuple[CheckinQuestion, object]] = []

    for item in payload.answers:
        if item.question_code in seen_question_codes:
            raise HTTPException(
                status_code=400,
                detail=f"Duplicate answer for question_code={item.question_code}",
            )
        seen_question_codes.add(item.question_code)

        question = questions_map.get(item.question_code)
        if not question:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown or inactive question_code={item.question_code}",
            )

        if question.answer_type == "scale_0_3":
            if item.score_value is None:
                raise HTTPException(
                    status_code=400,
                    detail=f"score_value is required for {item.question_code}",
                )
            normalized_answers.append((question, item))

            if question.code in NASAL_CODES:
                nasal_score += item.score_value
            elif question.code in OCULAR_CODES:
                ocular_score += item.score_value
            elif question.code == "wellbeing_today":
                wellbeing_score = item.score_value
            elif question.code == "activity_impact":
                activity_impact_score = item.score_value
            elif question.code == "sleep_impact":
                sleep_impact_score = item.score_value

        elif question.answer_type == "boolean":
            if item.bool_value is None:
                raise HTTPException(
                    status_code=400,
                    detail=f"bool_value is required for {item.question_code}",
                )
            normalized_answers.append((question, item))
            if question.code == "had_allergen_contact":
                had_allergen_contact = item.bool_value

        elif question.answer_type == "single_choice":
            if item.choice_value is None:
                raise HTTPException(
                    status_code=400,
                    detail=f"choice_value is required for {item.question_code}",
                )
            normalized_answers.append((question, item))
            if question.code == "possible_trigger":
                trigger_note = item.choice_value

        elif question.answer_type == "multi_choice":
            if item.choice_values_json is None:
                raise HTTPException(
                    status_code=400,
                    detail=f"choice_values_json is required for {item.question_code}",
                )
            normalized_answers.append((question, item))

        elif question.answer_type == "text":
            if item.text_value is None:
                raise HTTPException(
                    status_code=400,
                    detail=f"text_value is required for {item.question_code}",
                )
            normalized_answers.append((question, item))
            if question.code == "daily_note":
                note = item.text_value

        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported answer_type={question.answer_type}",
            )

    # validate medication usage
    seen_medication_ids: set[int] = set()
    for med_item in payload.medication_usage:
        if med_item.patient_medication_id in seen_medication_ids:
            raise HTTPException(
                status_code=400,
                detail=f"Duplicate medication usage for patient_medication_id={med_item.patient_medication_id}",
            )
        seen_medication_ids.add(med_item.patient_medication_id)

        if med_item.patient_medication_id not in owned_medications_map:
            raise HTTPException(
                status_code=400,
                detail=f"Medication course {med_item.patient_medication_id} does not belong to current user",
            )

        if med_item.effect is not None and med_item.effect not in ALLOWED_MED_EFFECTS:
            raise HTTPException(
                status_code=400,
                detail="Medication effect must be one of: good, partial, none",
            )

    symptom_total_score = nasal_score + ocular_score
    medication_score = calculate_medication_score(len(payload.medication_usage))
    day_total_score = symptom_total_score + medication_score
    severity_level = get_severity_level(symptom_total_score)

    checkin = await _get_owned_checkin(user.id, checkin_date, db)

    if not checkin:
        checkin = DailyCheckin(
            user_id=user.id,
            checkin_date=checkin_date,
        )
        db.add(checkin)
        await db.flush()

    checkin.nasal_score = nasal_score
    checkin.ocular_score = ocular_score
    checkin.symptom_total_score = symptom_total_score
    checkin.medication_score = medication_score
    checkin.day_total_score = day_total_score
    checkin.severity_level = severity_level

    checkin.wellbeing_score = wellbeing_score
    checkin.activity_impact_score = activity_impact_score
    checkin.sleep_impact_score = sleep_impact_score

    checkin.had_allergen_contact = had_allergen_contact
    checkin.trigger_note = trigger_note
    checkin.note = note

    # Replace answers
    await db.execute(
        delete(DailyCheckinAnswer).where(DailyCheckinAnswer.checkin_id == checkin.id)
    )

    for question, item in normalized_answers:
        db.add(
            DailyCheckinAnswer(
                checkin_id=checkin.id,
                question_id=question.id,
                score_value=item.score_value,
                bool_value=item.bool_value,
                text_value=item.text_value,
                choice_value=item.choice_value,
                choice_values_json=item.choice_values_json,
            )
        )

    # Replace daily medication usage
    await db.execute(
        delete(DailyMedicationUsage).where(DailyMedicationUsage.checkin_id == checkin.id)
    )

    for med_item in payload.medication_usage:
        db.add(
            DailyMedicationUsage(
                checkin_id=checkin.id,
                patient_medication_id=med_item.patient_medication_id,
                times_taken=med_item.times_taken,
                effect=med_item.effect,
                note=med_item.note,
            )
        )

    await db.commit()
    await db.refresh(checkin)

    return await _serialize_checkin(checkin, db)


@router.get("/calendar/month", response_model=CalendarMonthOut)
async def get_my_checkins_calendar_month(
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _, last_day = calendar.monthrange(year, month)
    start_date = date(year, month, 1)
    end_date = date(year, month, last_day)

    res = await db.execute(
        select(DailyCheckin)
        .where(
            DailyCheckin.user_id == user.id,
            DailyCheckin.checkin_date >= start_date,
            DailyCheckin.checkin_date <= end_date,
        )
        .order_by(DailyCheckin.checkin_date.asc())
    )
    rows = res.scalars().all()

    return CalendarMonthOut(
        year=year,
        month=month,
        days=[
            CalendarDayOut(
                date=row.checkin_date,
                symptom_total_score=row.symptom_total_score,
                medication_score=row.medication_score,
                day_total_score=row.day_total_score,
                severity_level=row.severity_level,
            )
            for row in rows
        ],
    )


@router.get("", response_model=list[DailyCheckinOut])
async def list_my_checkins(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(DailyCheckin)
        .where(DailyCheckin.user_id == user.id)
        .order_by(DailyCheckin.checkin_date.desc(), DailyCheckin.id.desc())
    )
    checkins = res.scalars().all()

    result: list[DailyCheckinOut] = []
    for item in checkins:
        result.append(await _serialize_checkin(item, db))
    return result
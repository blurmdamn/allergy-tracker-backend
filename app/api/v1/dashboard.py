from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.asit import AsitEvent, AsitPlan
from app.models.checkins import DailyCheckin
from app.models.meds import PatientMedication
from app.models.users import User
from app.schemas.dashboard import (
    DashboardNextAsitEventOut,
    DashboardOut,
    DashboardTodayCheckinOut,
)

router = APIRouter(prefix="/me/dashboard", tags=["Dashboard"])


async def _calculate_checkin_streak(user_id: int, db: AsyncSession, today: date) -> int:
    """
    Считаем подряд идущие дни с заполненными check-in.
    Логика:
    - если check-in сегодня есть -> считаем с today назад
    - если check-in сегодня нет, но вчера есть -> считаем с yesterday назад
    - иначе streak = 0
    """
    recent_res = await db.execute(
        select(DailyCheckin.checkin_date)
        .where(
            DailyCheckin.user_id == user_id,
            DailyCheckin.checkin_date <= today,
        )
        .order_by(DailyCheckin.checkin_date.desc())
    )
    dates = list(recent_res.scalars().all())
    if not dates:
        return 0

    date_set = set(dates)

    if today in date_set:
        cursor = today
    elif (today - timedelta(days=1)) in date_set:
        cursor = today - timedelta(days=1)
    else:
        return 0

    streak = 0
    while cursor in date_set:
        streak += 1
        cursor -= timedelta(days=1)

    return streak


@router.get("", response_model=DashboardOut)
async def get_my_dashboard(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    today = date.today()
    seven_days_ago = today - timedelta(days=6)

    # -------------------------
    # Today check-in
    # -------------------------
    today_res = await db.execute(
        select(DailyCheckin).where(
            DailyCheckin.user_id == user.id,
            DailyCheckin.checkin_date == today,
        )
    )
    today_checkin = today_res.scalar_one_or_none()

    today_checkin_out = DashboardTodayCheckinOut(
        date=today,
        filled=today_checkin is not None,
        severity_level=today_checkin.severity_level if today_checkin else None,
        nasal_score=today_checkin.nasal_score if today_checkin else None,
        ocular_score=today_checkin.ocular_score if today_checkin else None,
        symptom_total_score=today_checkin.symptom_total_score if today_checkin else None,
        medication_score=today_checkin.medication_score if today_checkin else None,
        day_total_score=today_checkin.day_total_score if today_checkin else None,
    )

    # -------------------------
    # Active medications count
    # -------------------------
    active_meds_res = await db.execute(
        select(func.count(PatientMedication.id)).where(
            PatientMedication.user_id == user.id,
            PatientMedication.is_active.is_(True),
        )
    )
    active_medications_count = int(active_meds_res.scalar() or 0)

    # -------------------------
    # Next ASIT event
    # Без relationship: join вручную через AsitPlan.id == AsitEvent.plan_id
    # -------------------------
    next_asit_res = await db.execute(
        select(AsitEvent)
        .join(AsitPlan, AsitPlan.id == AsitEvent.plan_id)
        .where(
            AsitPlan.user_id == user.id,
            AsitEvent.planned_date >= today,
            AsitEvent.status.in_(("planned", "rescheduled")),
        )
        .order_by(AsitEvent.planned_date.asc(), AsitEvent.id.asc())
        .limit(1)
    )
    next_asit = next_asit_res.scalar_one_or_none()

    next_asit_out = (
        DashboardNextAsitEventOut(
            id=next_asit.id,
            plan_id=next_asit.plan_id,
            planned_date=next_asit.planned_date,
            actual_date=next_asit.actual_date,
            status=next_asit.status,
            dose_value=next_asit.dose_value,
            note=next_asit.note,
        )
        if next_asit
        else None
    )

    # -------------------------
    # Severe days in last 7 days
    # -------------------------
    severe_days_res = await db.execute(
        select(func.count(DailyCheckin.id)).where(
            DailyCheckin.user_id == user.id,
            DailyCheckin.checkin_date >= seven_days_ago,
            DailyCheckin.checkin_date <= today,
            DailyCheckin.severity_level == "severe",
        )
    )
    severe_days_last_7 = int(severe_days_res.scalar() or 0)

    # -------------------------
    # Streak
    # -------------------------
    streak = await _calculate_checkin_streak(user.id, db, today)

    return DashboardOut(
        today_checkin=today_checkin_out,
        active_medications_count=active_medications_count,
        next_asit_event=next_asit_out,
        severe_days_last_7=severe_days_last_7,
        streak=streak,
    )
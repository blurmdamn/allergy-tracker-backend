from datetime import timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.dicts import Medication
from app.models.meds import MedicationIntakeLog, PatientMedication
from app.models.users import User
from app.schemas.meds import (
    MedicationIntakeLogCreate,
    MedicationIntakeLogOut,
    PatientMedicationCreate,
    PatientMedicationOut,
    PatientMedicationUpdate,
)

router = APIRouter(prefix="/me/medications", tags=["Medications"])

ALLOWED_EFFECTS = {"good", "partial", "none"}


def _make_naive_datetime(value):
    if value is None:
        return None

    if value.tzinfo is not None:
        return value.astimezone(timezone.utc).replace(tzinfo=None)

    return value


async def _resolve_medication_id(code: str | None, db: AsyncSession) -> int | None:
    if not code:
        return None

    res = await db.execute(select(Medication).where(Medication.code == code))
    medication = res.scalar_one_or_none()

    if not medication:
        raise HTTPException(status_code=400, detail=f"Unknown medication code: {code}")

    return medication.id


async def _get_medication_code_by_id(
    medication_id: int | None,
    db: AsyncSession,
) -> str | None:
    if medication_id is None:
        return None

    res = await db.execute(select(Medication.code).where(Medication.id == medication_id))
    return res.scalar_one_or_none()


async def _get_owned_patient_medication_or_404(
    med_id: int,
    user_id: int,
    db: AsyncSession,
) -> PatientMedication:
    res = await db.execute(
        select(PatientMedication).where(
            PatientMedication.id == med_id,
            PatientMedication.user_id == user_id,
        )
    )
    item = res.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="Medication course not found")

    return item


async def _serialize_patient_medication(
    item: PatientMedication,
    db: AsyncSession,
) -> PatientMedicationOut:
    return PatientMedicationOut(
        id=item.id,
        medication_code=await _get_medication_code_by_id(item.medication_id, db),
        dose_text=item.dose_text,
        times_per_day=item.times_per_day,
        interval_hours=item.interval_hours,
        treatment_effect=item.treatment_effect,
        started_at=item.started_at,
        ended_at=item.ended_at,
        is_active=item.is_active,
    )


@router.get("", response_model=list[PatientMedicationOut])
async def list_my_medications(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(PatientMedication)
        .where(PatientMedication.user_id == user.id)
        .order_by(
            PatientMedication.is_active.desc(),
            PatientMedication.started_at.desc(),
            PatientMedication.id.desc(),
        )
    )
    items = list(res.scalars().all())

    result: list[PatientMedicationOut] = []
    for item in items:
        result.append(await _serialize_patient_medication(item, db))

    return result


@router.post("", response_model=PatientMedicationOut)
async def create_my_medication(
    payload: PatientMedicationCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    medication_id = await _resolve_medication_id(payload.medication_code, db)

    if payload.started_at and payload.ended_at and payload.ended_at < payload.started_at:
        raise HTTPException(
            status_code=400,
            detail="ended_at cannot be earlier than started_at",
        )

    if payload.treatment_effect is not None and payload.treatment_effect not in ALLOWED_EFFECTS:
        raise HTTPException(
            status_code=400,
            detail="treatment_effect must be one of: good, partial, none",
        )

    item = PatientMedication(
        user_id=user.id,
        medication_id=medication_id,
        dose_text=payload.dose_text,
        times_per_day=payload.times_per_day,
        interval_hours=payload.interval_hours,
        treatment_effect=payload.treatment_effect,
        started_at=payload.started_at,
        ended_at=payload.ended_at,
        is_active=True,
    )

    db.add(item)
    await db.commit()
    await db.refresh(item)

    return await _serialize_patient_medication(item, db)


@router.get("/{med_id}", response_model=PatientMedicationOut)
async def get_my_medication(
    med_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    item = await _get_owned_patient_medication_or_404(
        med_id=med_id,
        user_id=user.id,
        db=db,
    )

    return await _serialize_patient_medication(item, db)


@router.patch("/{med_id}", response_model=PatientMedicationOut)
async def update_my_medication(
    med_id: int,
    payload: PatientMedicationUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    item = await _get_owned_patient_medication_or_404(
        med_id=med_id,
        user_id=user.id,
        db=db,
    )

    update_data = payload.model_dump(exclude_unset=True)

    if "medication_code" in update_data:
        item.medication_id = await _resolve_medication_id(
            update_data["medication_code"],
            db,
        )

    if "dose_text" in update_data:
        item.dose_text = update_data["dose_text"]

    if "times_per_day" in update_data:
        item.times_per_day = update_data["times_per_day"]

    if "interval_hours" in update_data:
        item.interval_hours = update_data["interval_hours"]

    if "treatment_effect" in update_data:
        treatment_effect = update_data["treatment_effect"]

        if treatment_effect is not None and treatment_effect not in ALLOWED_EFFECTS:
            raise HTTPException(
                status_code=400,
                detail="treatment_effect must be one of: good, partial, none",
            )

        item.treatment_effect = treatment_effect

    if "started_at" in update_data:
        item.started_at = update_data["started_at"]

    if "ended_at" in update_data:
        item.ended_at = update_data["ended_at"]

    if item.started_at and item.ended_at and item.ended_at < item.started_at:
        raise HTTPException(
            status_code=400,
            detail="ended_at cannot be earlier than started_at",
        )

    if "is_active" in update_data:
        item.is_active = update_data["is_active"]

    await db.commit()
    await db.refresh(item)

    return await _serialize_patient_medication(item, db)


@router.get("/{med_id}/logs", response_model=list[MedicationIntakeLogOut])
async def list_my_medication_logs(
    med_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_owned_patient_medication_or_404(
        med_id=med_id,
        user_id=user.id,
        db=db,
    )

    res = await db.execute(
        select(MedicationIntakeLog)
        .where(MedicationIntakeLog.patient_medication_id == med_id)
        .order_by(
            MedicationIntakeLog.logged_at.desc(),
            MedicationIntakeLog.id.desc(),
        )
    )

    logs = res.scalars().all()
    return [MedicationIntakeLogOut.model_validate(log) for log in logs]


@router.post("/{med_id}/logs", response_model=MedicationIntakeLogOut)
async def create_my_medication_log(
    med_id: int,
    payload: MedicationIntakeLogCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_owned_patient_medication_or_404(
        med_id=med_id,
        user_id=user.id,
        db=db,
    )

    if payload.effect is not None and payload.effect not in ALLOWED_EFFECTS:
        raise HTTPException(
            status_code=400,
            detail="effect must be one of: good, partial, none",
        )

    log_data = {
        "patient_medication_id": med_id,
        "dose_taken": payload.dose_taken,
        "effect": payload.effect,
        "note": payload.note,
    }

    if payload.intake_date is not None:
        log_data["logged_at"] = _make_naive_datetime(payload.intake_date)

    log = MedicationIntakeLog(**log_data)

    db.add(log)
    await db.commit()
    await db.refresh(log)

    return MedicationIntakeLogOut.model_validate(log)
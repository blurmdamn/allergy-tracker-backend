from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.allergy import (
    PatientAllergy,
    PatientAllergyMonth,
    patient_allergen,
    patient_symptom,
)
from app.models.dicts import Allergen, Symptom
from app.models.users import User
from app.schemas.allergy import AllergyOut, AllergyUpdate

router = APIRouter(prefix="/me", tags=["Me"])


def _normalize_months(months: list[int]) -> list[int]:
    uniq = sorted(set(months))
    if any(m < 1 or m > 12 for m in uniq):
        raise HTTPException(status_code=400, detail="active_months must be in range 1..12")
    return uniq


async def _get_active_months(db: AsyncSession, user_id: int) -> list[int]:
    res = await db.execute(
        select(PatientAllergyMonth.month_no)
        .where(PatientAllergyMonth.user_id == user_id)
        .order_by(PatientAllergyMonth.month_no.asc())
    )
    return list(res.scalars().all())


@router.get("/allergy", response_model=AllergyOut)
async def get_my_allergy(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(PatientAllergy).where(PatientAllergy.user_id == user.id))
    allergy = res.scalar_one_or_none()

    if not allergy:
        return AllergyOut(
            symptoms_start_date=None,
            active_months=[],
            frequency=None,
            allergen_codes=[],
            symptom_codes=[],
        )

    active_months = await _get_active_months(db, user.id)

    res_a = await db.execute(
        select(Allergen.code)
        .join(patient_allergen, patient_allergen.c.allergen_id == Allergen.id)
        .where(patient_allergen.c.user_id == user.id)
        .order_by(Allergen.name.asc())
    )
    allergen_codes = list(res_a.scalars().all())

    res_s = await db.execute(
        select(Symptom.code)
        .join(patient_symptom, patient_symptom.c.symptom_id == Symptom.id)
        .where(patient_symptom.c.user_id == user.id)
        .order_by(Symptom.name.asc())
    )
    symptom_codes = list(res_s.scalars().all())

    return AllergyOut(
        symptoms_start_date=allergy.symptoms_start_date,
        active_months=active_months,
        frequency=allergy.frequency,
        allergen_codes=allergen_codes,
        symptom_codes=symptom_codes,
    )


@router.put("/allergy", response_model=AllergyOut)
async def update_my_allergy(
    payload: AllergyUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(PatientAllergy).where(PatientAllergy.user_id == user.id))
    allergy = res.scalar_one_or_none()

    if not allergy:
        allergy = PatientAllergy(user_id=user.id)
        db.add(allergy)
        await db.flush()

    if payload.symptoms_start_date is not None:
        allergy.symptoms_start_date = payload.symptoms_start_date

    if payload.frequency is not None:
        if payload.frequency not in ("contact_only", "daily"):
            raise HTTPException(status_code=400, detail="frequency must be 'contact_only' or 'daily'")
        allergy.frequency = payload.frequency

    if payload.active_months is not None:
        months = _normalize_months(payload.active_months)
        await db.execute(delete(PatientAllergyMonth).where(PatientAllergyMonth.user_id == user.id))
        if months:
            db.add_all([PatientAllergyMonth(user_id=user.id, month_no=m) for m in months])

    if payload.allergen_codes is not None:
        if len(payload.allergen_codes) == 0:
            await db.execute(delete(patient_allergen).where(patient_allergen.c.user_id == user.id))
        else:
            res_ids = await db.execute(
                select(Allergen.id, Allergen.code).where(Allergen.code.in_(payload.allergen_codes))
            )
            rows = res_ids.all()
            found_codes = {code for (_, code) in rows}
            missing = [c for c in payload.allergen_codes if c not in found_codes]
            if missing:
                raise HTTPException(status_code=400, detail=f"Unknown allergen codes: {missing}")

            allergen_ids = [aid for (aid, _) in rows]
            await db.execute(delete(patient_allergen).where(patient_allergen.c.user_id == user.id))
            await db.execute(
                insert(patient_allergen),
                [{"user_id": user.id, "allergen_id": aid} for aid in allergen_ids],
            )

    if payload.symptom_codes is not None:
        if len(payload.symptom_codes) == 0:
            await db.execute(delete(patient_symptom).where(patient_symptom.c.user_id == user.id))
        else:
            res_ids = await db.execute(
                select(Symptom.id, Symptom.code).where(Symptom.code.in_(payload.symptom_codes))
            )
            rows = res_ids.all()
            found_codes = {code for (_, code) in rows}
            missing = [c for c in payload.symptom_codes if c not in found_codes]
            if missing:
                raise HTTPException(status_code=400, detail=f"Unknown symptom codes: {missing}")

            symptom_ids = [sid for (sid, _) in rows]
            await db.execute(delete(patient_symptom).where(patient_symptom.c.user_id == user.id))
            await db.execute(
                insert(patient_symptom),
                [{"user_id": user.id, "symptom_id": sid} for sid in symptom_ids],
            )

    await db.commit()
    return await get_my_allergy(user=user, db=db)

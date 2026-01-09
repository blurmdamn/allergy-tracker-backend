from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.models.dicts import Allergen, Symptom, Medication
from app.schemas.dicts import DictItem, MedicationItem

router = APIRouter(prefix="/dict", tags=["Dictionaries"])


@router.get("/allergens", response_model=list[DictItem])
async def list_allergens(db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Allergen).order_by(Allergen.name.asc()))
    items = res.scalars().all()
    return [DictItem(code=i.code, name=i.name) for i in items]


@router.get("/symptoms", response_model=list[DictItem])
async def list_symptoms(db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Symptom).order_by(Symptom.name.asc()))
    items = res.scalars().all()
    return [DictItem(code=i.code, name=i.name) for i in items]


@router.get("/medications", response_model=list[MedicationItem])
async def list_medications(
    form: str | None = Query(default=None, description="tablet | sl_drops | sl_tablet | injection"),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Medication)
    if form:
        stmt = stmt.where(Medication.form == form)
    stmt = stmt.order_by(Medication.form.asc(), Medication.name.asc())

    res = await db.execute(stmt)
    items = res.scalars().all()
    return [MedicationItem(code=i.code, name=i.name, form=i.form) for i in items]

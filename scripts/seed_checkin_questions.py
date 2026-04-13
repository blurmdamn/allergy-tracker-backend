import asyncio
from sqlalchemy.dialects.postgresql import insert

from app.db.session import AsyncSessionLocal
from app.models.checkins import CheckinQuestion

QUESTIONS = [
    # ---------------------------
    # Nasal symptoms
    # ---------------------------
    {
        "code": "runny_nose",
        "text": "Насморк сегодня",
        "domain": "nasal",
        "answer_type": "scale_0_3",
        "sort_order": 10,
        "is_active": True,
    },
    {
        "code": "nasal_congestion",
        "text": "Заложенность носа сегодня",
        "domain": "nasal",
        "answer_type": "scale_0_3",
        "sort_order": 20,
        "is_active": True,
    },
    {
        "code": "sneezing",
        "text": "Чихание сегодня",
        "domain": "nasal",
        "answer_type": "scale_0_3",
        "sort_order": 30,
        "is_active": True,
    },
    {
        "code": "itchy_nose",
        "text": "Зуд в носу сегодня",
        "domain": "nasal",
        "answer_type": "scale_0_3",
        "sort_order": 40,
        "is_active": True,
    },

    # ---------------------------
    # Ocular symptoms
    # ---------------------------
    {
        "code": "red_eyes",
        "text": "Покраснение глаз сегодня",
        "domain": "ocular",
        "answer_type": "scale_0_3",
        "sort_order": 50,
        "is_active": True,
    },
    {
        "code": "watery_eyes",
        "text": "Слезоточивость глаз сегодня",
        "domain": "ocular",
        "answer_type": "scale_0_3",
        "sort_order": 60,
        "is_active": True,
    },
    {
        "code": "itchy_eyes",
        "text": "Зуд глаз сегодня",
        "domain": "ocular",
        "answer_type": "scale_0_3",
        "sort_order": 70,
        "is_active": True,
    },

    # ---------------------------
    # Daily impact / quality of life
    # ---------------------------
    {
        "code": "wellbeing_today",
        "text": "Как вы себя чувствуете сегодня?",
        "domain": "wellbeing",
        "answer_type": "scale_0_3",
        "sort_order": 80,
        "is_active": True,
    },
    {
        "code": "activity_impact",
        "text": "Повлияли ли симптомы на вашу активность сегодня?",
        "domain": "activity",
        "answer_type": "scale_0_3",
        "sort_order": 90,
        "is_active": True,
    },
    {
        "code": "sleep_impact",
        "text": "Были ли нарушения сна из-за симптомов?",
        "domain": "sleep",
        "answer_type": "scale_0_3",
        "sort_order": 100,
        "is_active": True,
    },

    # ---------------------------
    # Triggers
    # ---------------------------
    {
        "code": "had_allergen_contact",
        "text": "Был ли сегодня контакт с аллергеном?",
        "domain": "trigger",
        "answer_type": "boolean",
        "sort_order": 110,
        "is_active": True,
    },
    {
        "code": "possible_trigger",
        "text": "Что могло вызвать ухудшение сегодня?",
        "domain": "trigger",
        "answer_type": "single_choice",
        "sort_order": 120,
        "is_active": True,
    },

    # ---------------------------
    # Medication
    # ---------------------------
    {
        "code": "meds_taken_today",
        "text": "Принимали ли вы сегодня препараты от аллергии?",
        "domain": "medication",
        "answer_type": "boolean",
        "sort_order": 130,
        "is_active": True,
    },

    # ---------------------------
    # Free text note
    # ---------------------------
    {
        "code": "daily_note",
        "text": "Заметка за день",
        "domain": "note",
        "answer_type": "text",
        "sort_order": 140,
        "is_active": True,
    },
]


async def upsert_questions(session, rows: list[dict]):
    if not rows:
        return

    stmt = insert(CheckinQuestion).values(rows)
    update_cols = {
        c: getattr(stmt.excluded, c)
        for c in rows[0].keys()
        if c != "code"
    }
    stmt = stmt.on_conflict_do_update(
        index_elements=["code"],
        set_=update_cols,
    )
    await session.execute(stmt)


async def main():
    async with AsyncSessionLocal() as session:
        try:
            await upsert_questions(session, QUESTIONS)
            await session.commit()
            print("✅ Check-in questions seeded.")
        except Exception:
            await session.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(main())
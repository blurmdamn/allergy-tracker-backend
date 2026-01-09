import asyncio
from sqlalchemy.dialects.postgresql import insert

from app.db.session import AsyncSessionLocal
from app.models.dicts import Allergen, Symptom, Medication

ALLERGENS = [
    {"code": "birch", "name": "берёза"},
    {"code": "alder", "name": "ольха"},
    {"code": "oak", "name": "дуб"},
    {"code": "timothy_grass", "name": "тимофеевка"},
    {"code": "meadow_grass", "name": "мятлик"},
    {"code": "mugwort", "name": "полынь"},
    {"code": "ragweed", "name": "амброзия"},
    {"code": "chenopodium", "name": "марь"},
    {"code": "lambs_quarters", "name": "лебеда"},
    {"code": "kochia", "name": "курай"},
    {"code": "d_pteronyssinus", "name": "клещ дерматофагоид птерониссинус"},
    {"code": "d_farinae", "name": "клещ дерматофагоид фарине"},
    {"code": "alternaria", "name": "плесень альтернария"},
    {"code": "cladosporium", "name": "плесень кладоспориум"},
    {"code": "aspergillus", "name": "плесень аспергиллус"},
    {"code": "cat", "name": "кошка"},
    {"code": "dog", "name": "собака"},
    {"code": "horse", "name": "лошадь"},
]

SYMPTOMS = [
    {"code": "runny_nose", "name": "насморк"},
    {"code": "nasal_congestion", "name": "заложенность носа"},
    {"code": "sneezing", "name": "чихание"},
    {"code": "itchy_nose", "name": "зуд в носу"},
    {"code": "red_eyes", "name": "покраснение глаз"},
    {"code": "watery_eyes", "name": "слезоточивость глаз"},
    {"code": "itchy_eyes", "name": "зуд глаз"},
]

MEDICATIONS = [
    # Таблетки
    {"code": "cetirizine", "name": "цетиризин", "form": "tablet"},
    {"code": "levocetirizine", "name": "левоцетиризин", "form": "tablet"},
    {"code": "loratadine", "name": "лоратадин", "form": "tablet"},
    {"code": "desloratadine", "name": "дезлоратадин", "form": "tablet"},
    {"code": "bilastine", "name": "биластин", "form": "tablet"},
    {"code": "fexofenadine", "name": "фексофенадин", "form": "tablet"},
    {"code": "ebastine", "name": "эбастин", "form": "tablet"},
    {"code": "rupatadine", "name": "рупатадин", "form": "tablet"},
    {"code": "montelukast", "name": "монтелукаст", "form": "tablet"},

    # Подъязычные капли
    {"code": "roxall_sulgen", "name": "Роксаль Сульген", "form": "sl_drops"},
    {"code": "immunotek_oraltek", "name": "Инмунотек Оралтек", "form": "sl_drops"},

    # Подъязычные таблетки
    {"code": "lofharma", "name": "Лофарма", "form": "sl_tablet"},
    {"code": "antipollin", "name": "антиполлин", "form": "sl_tablet"},

    # Инъекции
    {"code": "roxall_clastoid", "name": "Роксаль Кластоид", "form": "injection"},
    {"code": "immunotek_clustek", "name": "Инмунотек Клюстек", "form": "injection"},
]

async def upsert_all(session, model, rows, conflict_cols: list[str]):
    stmt = insert(model).values(rows)
    update_cols = {c: getattr(stmt.excluded, c) for c in rows[0].keys() if c not in conflict_cols}
    stmt = stmt.on_conflict_do_update(index_elements=conflict_cols, set_=update_cols)
    await session.execute(stmt)

async def main():
    async with AsyncSessionLocal() as session:
        await upsert_all(session, Allergen, ALLERGENS, conflict_cols=["code"])
        await upsert_all(session, Symptom, SYMPTOMS, conflict_cols=["code"])
        await upsert_all(session, Medication, MEDICATIONS, conflict_cols=["code"])
        await session.commit()
    print("✅ Dictionaries seeded (allergens, symptoms, medications).")

if __name__ == "__main__":
    asyncio.run(main())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
# from app.database import init_db 

# Создание экземпляра приложения FastAPI
app = FastAPI(
    title="Allergy Tracker API",
    description="Backend API for PWA Seasonal Allergy Monitoring.",
    version="0.1.0"
)

# # --- Настройка CORS (Cross-Origin Resource Sharing) ---
# # Это позволяет вашему фронтенду на React обращаться к API.
# origins = [
#     "http://localhost:3000",
#     "http://127.0.0.1:3000",
        # http://localhost:8001",   # <-- ДОБАВЬТЕ ЭТОТ ПОРТ (и любой другой, который вы используете)
        # "http://127.0.0.1:8001",
#     # Здесь будут адреса вашего PWA после развертывания
# ]

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # --- Хук для инициализации БД при запуске ---
# @app.on_event("startup")
# async def startup_event():
#     """
#     Выполняется при запуске сервера.
#     Инициализирует подключение к БД и создает все таблицы (если они не существуют).
#     """
#     print("Initializing database...")
#     try:
#         await init_db() 
#         print("Database initialized successfully: Tables created in PostgreSQL.")
#     except Exception as e:
#         print(f"Error initializing database: {e}")
#         # Здесь можно добавить логику для завершения работы, если БД недоступна

# --- Базовый Эндпоинт ---
@app.get("/")
def read_root():
    """Проверка доступности API."""
    return {"message": "Allergy Tracker API is Running!", "status": "ok"}

# --- Запуск ---
# Чтобы запустить: uvicorn main:app --reload
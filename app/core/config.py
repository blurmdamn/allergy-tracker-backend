from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )
    DATABASE_URL: str


    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

# email
    EMAIL_PROVIDER: str = "console"  # console | sendgrid | smtp (на будущее)
    SENDGRID_API_KEY: str | None = None
    EMAIL_FROM: str = "Allergy Tracker <no-reply@example.com>"
    FRONTEND_BASE_URL: str = "http://localhost:3000"
    

# telegram
    TELEGRAM_BOT_TOKEN: str | None = None
    TELEGRAM_BOT_USERNAME: str | None = None
    TELEGRAM_ENABLED: bool = False
    TELEGRAM_POLLING_ENABLED: bool = True
    TELEGRAM_POLLING_INTERVAL_SECONDS: int = 5
    TELEGRAM_REMINDER_INTERVAL_SECONDS: int = 60

    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]


settings = Settings()

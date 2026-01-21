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
    
settings = Settings()

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Portfolio API"
    DATABASE_URL: str = "sqlite:///portfolio.db"

    # --- Security Settings ---
    # Notice: No default values for secrets!
    # If they are missing from .env, Pydantic will crash the app (Fail-Fast principle).
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 1 week

    ADMIN_USERNAME: str
    ADMIN_PASSWORD: str

    # Environment flag (development / production)
    ENVIRONMENT: str = "development"

    # --- File Upload Settings ---
    MEDIA_ROOT: str = "uploads"  # Physical directory on disk
    MEDIA_URL: str = "/uploads"  # URL prefix for the web

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()

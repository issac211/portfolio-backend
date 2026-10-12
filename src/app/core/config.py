from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Portfolio API"
    PROJECT_VERSION: str = "1.1.1"
    DATABASE_URL: str = "sqlite:///portfolio.db"

    @field_validator("DATABASE_URL", mode="after")
    @classmethod
    def assemble_db_connection(cls, v: str) -> str:
        """Ensure PostgreSQL connection strings use the psycopg2 driver dialect."""
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+psycopg2://", 1)
        if v.startswith("postgresql://") and not v.startswith("postgresql+"):
            return v.replace("postgresql://", "postgresql+psycopg2://", 1)
        return v

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

    # NEW: 5 Megabytes (5 * 1024 * 1024 bytes)
    MAX_IMAGE_SIZE_BYTES: int = 5242880

    # --- Cloud Storage (Cloudinary - Production) ---
    CLOUDINARY_URL: str | None = None

    # --- CORS Settings ---
    # Comma-separated list of allowed origin URLs (e.g. "http://localhost:5173,https://myfrontend.com")
    ALLOWED_ORIGINS: str = "http://localhost:5173"

    @property
    def allowed_origins_list(self) -> list[str]:
        """Convert comma-separated ALLOWED_ORIGINS into a sanitized list of origins."""
        parsed = [
            origin.strip().rstrip("/")
            for origin in self.ALLOWED_ORIGINS.split(",")
            if origin.strip()
        ]
        return parsed or ["http://localhost:5173"]

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()

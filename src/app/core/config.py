from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Portfolio API"
    # To move to Postgres later, you ONLY change this string to:
    # SQLALCHEMY_DATABASE_URL = "postgresql://user:password@localhost/dbname"
    DATABASE_URL: str = "sqlite:///portfolio.db"

    class Config:
        env_file = ".env"


settings = Settings()

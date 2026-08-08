from collections.abc import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core import SessionLocal
from app.services import PersonalInfoService, ProjectService


def get_db() -> Generator[Session, None, None]:
    """Provide a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_project_service(db: Session = Depends(get_db)) -> ProjectService:
    """Dependency injection factory for ProjectService."""
    return ProjectService(db)


def get_personal_info_service(db: Session = Depends(get_db)) -> PersonalInfoService:
    """Dependency injection factory for PersonalInfoService."""
    return PersonalInfoService(db)

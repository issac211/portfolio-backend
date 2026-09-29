import secrets
from collections.abc import Generator

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy.orm import Session

from app.core import SessionLocal, settings
from app.services import PersonalInfoService, ProjectService

# This tells FastAPI where the client can get the token (for Swagger UI)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_db() -> Generator[Session]:
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


def get_current_admin(token: str = Depends(oauth2_scheme)) -> str:
    """
    Dependency to protect routes.
    It reads the JWT token from the Authorization header and validates it.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username = payload.get("sub")
        if not username or not secrets.compare_digest(
            username, settings.ADMIN_USERNAME
        ):
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception

    return username

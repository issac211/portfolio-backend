import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core import create_access_token, settings
from app.schemas import Token

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Token:
    """
    Validates both username and password against the environment variables
    using constant-time comparison to prevent timing attacks.
    """
    is_username_valid = secrets.compare_digest(
        form_data.username, settings.ADMIN_USERNAME
    )
    is_password_valid = secrets.compare_digest(
        form_data.password, settings.ADMIN_PASSWORD
    )

    if not (is_username_valid and is_password_valid):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create the token encoding the username inside the payload ("sub" = subject)
    access_token = create_access_token(data={"sub": settings.ADMIN_USERNAME})

    return Token(access_token=access_token, token_type="bearer")

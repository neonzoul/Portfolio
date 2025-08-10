# :Modules: Dependencies
# === Purpose ===
# Reusable FastAPI dependencies such as DB session and current user resolver.

from __future__ import annotations

from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session
from jose import JWTError, jwt

from app.db.session import get_session
from app.core.config import settings
from app.repositories.users import UserRepository
from app.models.user import User


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")  # Bearer token (JWT)


def get_db() -> Generator[Session, None, None]:
    """Provide a SQLModel session per request."""
    yield from get_session()


def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    """Resolve and return the current authenticated user from a JWT bearer token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str | None = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user_repo = UserRepository(db)
    user = user_repo.get_by_email(email=email)

    if user is None:
        raise credentials_exception
    return user

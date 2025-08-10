from __future__ import annotations

from typing import Generator
from fastapi import Depends
from sqlmodel import Session, select

from app.db.session import get_session
from app.models.user import User


def get_db() -> Generator[Session, None, None]:
    yield from get_session()


def get_current_user(db: Session = Depends(get_db)) -> User:
    # Placeholder: in real app, extract from JWT. Here, return the first user.
    user = db.exec(select(User)).first()
    if not user:
        # Create a fallback demo user for local testing
        demo = User(name="Demo User", email="demo@example.com")
        db.add(demo)
        db.commit()
        db.refresh(demo)
        return demo
    return user

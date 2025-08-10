from __future__ import annotations

from sqlmodel import Session

from app.repositories.users import UserRepository
from app.core.security import verify_password
from app.schemas.users import UserCreate
from app.models.user import User


class UserService:
    def __init__(self, session: Session):
        self.repo = UserRepository(session)
        self.session = session

    def authenticate(self, email: str, password: str) -> User | None:
        user = self.repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):  # type: ignore[attr-defined]
            return None
        return user

    def create_user(self, user_create: UserCreate) -> User:
        user = self.repo.create(user_create)
        self.session.commit()
        self.session.refresh(user)
        return user

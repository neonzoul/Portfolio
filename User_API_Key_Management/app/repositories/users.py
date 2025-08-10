from __future__ import annotations

from sqlmodel import Session, select

from app.models.user import User
from app.schemas.users import UserCreate
from app.core.security import get_password_hash


class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email)
        return self.session.exec(statement).first()

    def create(self, user_create: UserCreate) -> User:
        hashed_password = get_password_hash(user_create.password)
        # Populate required 'name' using email local-part as a default
        default_name = user_create.email.split("@")[0]
        user = User(name=default_name, email=user_create.email, hashed_password=hashed_password)
        self.session.add(user)
        self.session.flush()
        return user

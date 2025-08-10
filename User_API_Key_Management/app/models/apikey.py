# API Key model
from __future__ import annotations # Enables modern, cleaner type hints for related models

from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional

from app.models.user import User

class ApiKeys(SQLModel, table=True):

    id: Optional[int] = Field(default=None, primary_key=True)
    key_prefix: str = Field(index=True, max_length=32)
    hashed_key: str
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), 
        index=True)

    user_id: int = Field(foreign_key="user.id", index=True)
    user: User = Relationship(back_populates="api_keys")
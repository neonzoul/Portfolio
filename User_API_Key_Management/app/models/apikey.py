# :Modules: API Key Model
# === Purpose ===
# SQLModel table representing hashed API keys belonging to users.

from __future__ import annotations  # Enables modern, cleaner type hints for related models

from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import User

class ApiKeys(SQLModel, table=True):

    # --- Columns ---
    id: int | None = Field(default=None, primary_key=True)
    key_prefix: str = Field(index=True, max_length=32)  # visible, non-secret prefix
    hashed_key: str  # irreversible bcrypt hash of the full key
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), 
        index=True)

    # --- Relationships ---
    user_id: int = Field(foreign_key="user.id", index=True)
    user: User = Relationship(back_populates="api_keys")


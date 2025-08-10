# :Modules: User Model
# === Purpose ===
# SQLModel table representing application users.

from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional, TYPE_CHECKING
from datetime import datetime, timezone

if TYPE_CHECKING:
    from .apikey import ApiKeys

class User(SQLModel, table=True):
    # --- Columns ---
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, max_length=100)
    email: str = Field(index=True, unique=True, max_length=100)
    hashed_password: str = Field(default="", nullable=False, max_length=255)
    created_at: datetime | None = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)

    # --- Relationships ---
    api_keys: List["ApiKeys"] = Relationship(back_populates="user")
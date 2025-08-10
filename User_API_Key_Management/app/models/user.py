from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional, TYPE_CHECKING
from datetime import datetime, timezone

if TYPE_CHECKING:
    from .apikey import ApiKeys

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, max_length=100)
    email: str = Field(index=True, unique=True, max_length=100)
    created_at: datetime | None = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)

    # Relationship
    api_keys: List["ApiKeys"] = Relationship(back_populates="user")
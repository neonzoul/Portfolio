from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .apikey import ApiKeys

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, max_length=100)
    email: str = Field(index=True, unique=True, max_length=100)
    created_at: Optional[str] = Field(default=None, index=True)

    # Relationship
    api_keys: List["ApiKeys"] = Relationship(back_populates="user")
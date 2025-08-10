# :Modules: User Schemas
# === Purpose ===
# Pydantic models for user creation and read views.

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserRead(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

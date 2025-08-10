from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class ApiKeyMeta(BaseModel):
    id: int
    key_prefix: str
    created_at: datetime

    class Config:
        from_attributes = True


class ApiKeyCreateResponse(ApiKeyMeta):
    # Only returned once on creation
    plaintext_key: str

# :Modules: API Key Schemas
# === Purpose ===
# Pydantic models for API key serialization.

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
    # Only returned once on creation (do not store this server-side)
    plaintext_key: str

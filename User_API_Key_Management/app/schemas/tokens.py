# :Modules: Token Schemas
# === Purpose ===
# Pydantic models for OAuth2/JWT tokens.

from __future__ import annotations

from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: str | None = None

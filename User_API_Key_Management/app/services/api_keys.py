# :Modules: API Key Service
# === Purpose ===
# Business logic for creating, listing, and revoking API keys.

from __future__ import annotations

from sqlmodel import Session
from fastapi import HTTPException, status

from app.core.security import generate_api_key, hash_api_key
from app.models.apikey import ApiKeys


class ApiKeyService:
    def __init__(self, session: Session):
        self.session = session

    def create_for_user(self, user_id: int) -> tuple[ApiKeys, str]:
        plaintext, prefix = generate_api_key()
        hashed = hash_api_key(plaintext)

        apikey = ApiKeys(key_prefix=prefix, hashed_key=hashed, user_id=user_id)
        self.session.add(apikey)
        self.session.commit()
        self.session.refresh(apikey)
        return apikey, plaintext

    def list_for_user(self, user_id: int) -> list[ApiKeys]:
        from app.repositories.api_keys import ApiKeyRepository

        repo = ApiKeyRepository(self.session)
        return repo.list_by_user(user_id)

    def revoke_for_user(self, user_id: int, key_id: int) -> None:
        from app.repositories.api_keys import ApiKeyRepository

        repo = ApiKeyRepository(self.session)
        apikey = repo.get(key_id)
        if not apikey:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
        if apikey.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to revoke this key")
        repo.delete(apikey)
        self.session.commit()

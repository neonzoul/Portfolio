from __future__ import annotations

from sqlmodel import Session

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

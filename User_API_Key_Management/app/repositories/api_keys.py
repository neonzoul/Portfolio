from __future__ import annotations

from typing import List, Optional
from sqlmodel import Session, select
from sqlalchemy import text

from app.models.apikey import ApiKeys


class ApiKeyRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, apikey: ApiKeys) -> ApiKeys:
        self.session.add(apikey)
        self.session.flush()
        return apikey

    def get(self, key_id: int) -> Optional[ApiKeys]:
        return self.session.get(ApiKeys, key_id)

    def list_by_user(self, user_id: int) -> List[ApiKeys]:
        # Order by created_at desc; using text to avoid typing issues with SQLModel field
        stmt = (
            select(ApiKeys)
            .where(ApiKeys.user_id == user_id)
            .order_by(text("created_at DESC"))
        )
        return list(self.session.exec(stmt))

    def delete(self, apikey: ApiKeys) -> None:
        self.session.delete(apikey)

    def count_by_user(self, user_id: int) -> int:
        stmt = select(ApiKeys).where(ApiKeys.user_id == user_id)
        return len(list(self.session.exec(stmt)))

# Assignment Guide: API Key Management

This document outlines the file structure and code for implementing the API Key Management feature using a clean, layered architecture with Services and Repositories.

## 📂 Proposed Project Structure (under `app/`)

This structure separates concerns into distinct layers, making the application testable and maintainable.

```
app/
├── api/
│   └── routers/
│       └── users_apikeys.py    # FastAPI routes only
├── core/
│   ├── config.py             # Settings (e.g., max keys per user)
│   ├── deps.py               # Dependency Injection: DB session, current user
│   └── security.py           # Key generation + hashing
├── db/
│   └── session.py            # SQLModel/Alembic session setup
├── models/
│   ├── user.py               # User model (+ relationship)
│   └── apikey.py             # ApiKey model
├── repositories/
│   └── api_keys.py           # Database I/O for ApiKey
├── schemas/
│   └── apikeys.py            # Pydantic DTOs for API responses
└── services/
    └── api_keys.py           # Business logic (create/list/revoke)
```

---

## 🛠️ Component Breakdown & Scaffolding

Here are the code snippets for each new file.

### 1\. Models (`app/models/`)

#### `app/models/apikey.py`

```python
from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship

class ApiKey(SQLModel, table=True):
    __tablename__ = "api_keys"

    id: Optional[int] = Field(default=None, primary_key=True)
    key_prefix: str = Field(index=True, max_length=32)
    hashed_key: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)

    user_id: int = Field(foreign_key="users.id", index=True)
    user: "User" = Relationship(back_populates="api_keys")
```

#### `app/models/user.py` (Update)

```python
# ...existing code...
from typing import List, Optional
from sqlmodel import Relationship
from .apikey import ApiKey

class User(SQLModel, table=True):
    # ...existing fields...
    api_keys: List[ApiKey] = Relationship(back_populates="user")
# ...existing code...
```

### 2\. Schemas (`app/schemas/apikeys.py`)

```python
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
```

### 3\. Core (`app/core/`)

#### `app/core/security.py`

```python
import secrets
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
PREFIX_NAMESPACE = "amos"  # AutomateOS Secret

def generate_api_key() -> tuple[str, str]:
    prefix_suffix = secrets.token_hex(4)
    key_prefix = f"{PREFIX_NAMESPACE}_{prefix_suffix}"
    random_part = secrets.token_urlsafe(32)
    plaintext_key = f"{key_prefix}.{random_part}"
    return plaintext_key, key_prefix

def hash_api_key(plain_key: str) -> str:
    return pwd_context.hash(plain_key)
```

#### `app/core/config.py`

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MAX_KEYS_PER_USER: int = 5

    class Config:
        env_file = ".env"

settings = Settings()
```

### 4\. Repository (`app/repositories/api_keys.py`)

```python
from typing import List, Optional
from sqlmodel import Session, select
from app.models.apikey import ApiKey

class ApiKeyRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, apikey: ApiKey) -> ApiKey:
        self.session.add(apikey)
        self.session.flush()
        return apikey

    def get(self, key_id: int) -> Optional[ApiKey]:
        return self.session.get(ApiKey, key_id)

    def list_by_user(self, user_id: int) -> List[ApiKey]:
        stmt = select(ApiKey).where(ApiKey.user_id == user_id).order_by(ApiKey.created_at.desc())
        return list(self.session.exec(stmt))

    def delete(self, apikey: ApiKey) -> None:
        self.session.delete(apikey)

    def count_by_user(self, user_id: int) -> int:
        stmt = select(ApiKey).where(ApiKey.user_id == user_id)
        return len(list(self.session.exec(stmt)))
```

### 5\. Service (`app/services/api_keys.py`)

```python
from fastapi import HTTPException, status
from sqlmodel import Session
from app.core.config import settings
from app.core.security import generate_api_key, hash_api_key
from app.models.apikey import ApiKey
from app.repositories.api_keys import ApiKeyRepository

class ApiKeyService:
    def __init__(self, session: Session):
        self.repo = ApiKeyRepository(session)
        self.session = session

    def create_for_user(self, user_id: int) -> tuple[ApiKey, str]:
        if self.repo.count_by_user(user_id) >= settings.MAX_KEYS_PER_USER:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="API key limit reached")

        plaintext, prefix = generate_api_key()
        hashed = hash_api_key(plaintext)

        apikey = ApiKey(key_prefix=prefix, hashed_key=hashed, user_id=user_id)
        self.repo.create(apikey)
        self.session.commit()
        self.session.refresh(apikey)
        return apikey, plaintext

    def list_for_user(self, user_id: int) -> list[ApiKey]:
        return self.repo.list_by_user(user_id)

    def revoke_for_user(self, user_id: int, key_id: int) -> None:
        apikey = self.repo.get(key_id)
        if not apikey:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
        if apikey.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to revoke this key")
        self.repo.delete(apikey)
        self.session.commit()
```

### 6\. API Router (`app/api/routers/users_apikeys.py`)

```python
from fastapi import APIRouter, Depends, status
from sqlmodel import Session
from app.core.deps import get_db, get_current_user # Assumes you have these
from app.schemas.apikeys import ApiKeyMeta, ApiKeyCreateResponse
from app.services.api_keys import ApiKeyService
from app.models.user import User # Assumes you have this

router = APIRouter(prefix="/users/me/apikeys", tags=["API Keys"])

@router.post("", response_model=ApiKeyCreateResponse, status_code=status.HTTP_201_CREATED)
def create_my_api_key(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = ApiKeyService(db)
    apikey, plaintext = svc.create_for_user(current_user.id)
    return ApiKeyCreateResponse(
        id=apikey.id,
        key_prefix=apikey.key_prefix,
        created_at=apikey.created_at,
        plaintext_key=plaintext,
    )

@router.get("", response_model=list[ApiKeyMeta])
def list_my_api_keys(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = ApiKeyService(db)
    return svc.list_for_user(current_user.id)

@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_api_key(
    key_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = ApiKeyService(db)
    svc.revoke_for_user(current_user.id, key_id)
    return None
```

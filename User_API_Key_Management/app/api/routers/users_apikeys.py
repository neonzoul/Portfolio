from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.apikeys import ApiKeyCreateResponse, ApiKeyMeta
from app.services.api_keys import ApiKeyService


router = APIRouter(prefix="/users/me/apikeys", tags=["API Keys"])


@router.post("", response_model=ApiKeyCreateResponse, status_code=status.HTTP_201_CREATED)
def create_my_api_key(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = ApiKeyService(db)
    apikey, plaintext = svc.create_for_user(current_user.id)  # type: ignore[arg-type]
    return ApiKeyCreateResponse(
        id=apikey.id,  # type: ignore[arg-type]
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
    return svc.list_for_user(current_user.id)  # type: ignore[arg-type]


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_api_key(
    key_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = ApiKeyService(db)
    svc.revoke_for_user(current_user.id, key_id)  # type: ignore[arg-type]
    return None

import secrets
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from afridock_api.auth.dependencies import (
    API_KEY_PREFIX,
    get_org_session,
    hash_api_key,
    require_role,
)
from afridock_api.db.models.api_key import ApiKey
from afridock_api.db.models.enums import UserRole
from afridock_api.db.models.user import User

router = APIRouter(prefix="/organizations/current/api-keys", tags=["api-keys"])

_KEY_PREVIEW_LENGTH = 8


class ApiKeyOut(BaseModel):
    id: uuid.UUID
    name: str
    keyPrefix: str
    createdAt: str
    lastUsedAt: str | None
    revokedAt: str | None


class CreateApiKeyRequest(BaseModel):
    name: str


class CreateApiKeyResponse(BaseModel):
    id: uuid.UUID
    name: str
    key: str
    keyPrefix: str


def _to_api_key_out(api_key: ApiKey) -> ApiKeyOut:
    return ApiKeyOut(
        id=api_key.id,
        name=api_key.name,
        keyPrefix=api_key.key_prefix,
        createdAt=api_key.created_at.isoformat(),
        lastUsedAt=api_key.last_used_at.isoformat() if api_key.last_used_at else None,
        revokedAt=api_key.revoked_at.isoformat() if api_key.revoked_at else None,
    )


@router.get("", response_model=list[ApiKeyOut])
async def list_api_keys(
    admin: User = Depends(require_role(UserRole.ADMIN)),
    session: AsyncSession = Depends(get_org_session),
) -> list[ApiKeyOut]:
    result = await session.execute(
        select(ApiKey).where(ApiKey.org_id == admin.org_id).order_by(ApiKey.created_at.desc())
    )
    return [_to_api_key_out(key) for key in result.scalars().all()]


@router.post("", response_model=CreateApiKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    body: CreateApiKeyRequest,
    admin: User = Depends(require_role(UserRole.ADMIN)),
    session: AsyncSession = Depends(get_org_session),
) -> CreateApiKeyResponse:
    """The plaintext key is returned exactly once, here — only its SHA-256
    hash is ever stored (see ApiKey's docstring for why SHA-256, not a
    password-style KDF, is the right choice for a high-entropy token)."""
    raw_key = API_KEY_PREFIX + secrets.token_urlsafe(32)
    api_key = ApiKey(
        org_id=admin.org_id,
        name=body.name,
        hashed_key=hash_api_key(raw_key),
        key_prefix=raw_key[:_KEY_PREVIEW_LENGTH],
        created_by=admin.id,
    )
    session.add(api_key)
    await session.flush()
    return CreateApiKeyResponse(
        id=api_key.id, name=api_key.name, key=raw_key, keyPrefix=api_key.key_prefix
    )


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: uuid.UUID,
    admin: User = Depends(require_role(UserRole.ADMIN)),
    session: AsyncSession = Depends(get_org_session),
) -> None:
    result = await session.execute(
        select(ApiKey).where(ApiKey.id == key_id, ApiKey.org_id == admin.org_id)
    )
    api_key = result.scalar_one_or_none()
    if api_key is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
    api_key.revoked_at = datetime.now(UTC)
    await session.flush()

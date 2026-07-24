import hashlib
import uuid
from collections.abc import AsyncGenerator, Callable, Coroutine
from datetime import UTC, datetime
from typing import Any

from fastapi import Depends, Header, HTTPException, status
from fastapi_users import FastAPIUsers
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from afridock_api.auth.backend import auth_backend
from afridock_api.auth.manager import get_user_manager
from afridock_api.db.models.api_key import ApiKey
from afridock_api.db.models.enums import UserRole
from afridock_api.db.models.user import User
from afridock_api.db.session import async_session_factory, org_scoped_session

fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])

current_active_user = fastapi_users.current_user(active=True, verified=True)
# Returns None instead of raising 401 when there's no valid session — lets
# get_org_id_via_cookie_or_api_key try API-key auth first without forcing a
# cookie to also be present.
_current_active_user_optional = fastapi_users.current_user(
    active=True, verified=True, optional=True
)

API_KEY_PREFIX = "afk_"


def hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


async def _org_id_from_api_key(raw_key: str) -> uuid.UUID:
    # No app.org_id is set yet at this point — this lookup is what
    # determines it (see the CASE WHEN carve-out on api_keys' RLS policy,
    # migration 0003, matching users/organizations in 0002).
    async with async_session_factory() as session:
        result = await session.execute(
            select(ApiKey).where(ApiKey.hashed_key == hash_api_key(raw_key))
        )
        api_key = result.scalar_one_or_none()
        if api_key is None or api_key.revoked_at is not None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid API key")
        api_key.last_used_at = datetime.now(UTC)
        await session.commit()
        return api_key.org_id


async def get_org_id_via_cookie_or_api_key(
    authorization: str | None = Header(default=None),
    user: User | None = Depends(_current_active_user_optional),
) -> uuid.UUID:
    """Authenticates via `Authorization: Bearer afk_...` (machine/API-key
    access, plan E5) if present, otherwise falls back to the normal cookie
    session. Use for routes that should be reachable both by the web app
    and by an org's own API key.
    """
    if authorization and authorization.startswith("Bearer ") and API_KEY_PREFIX in authorization:
        return await _org_id_from_api_key(authorization.removeprefix("Bearer ").strip())
    if user is not None:
        return user.org_id
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="authentication required")


async def get_org_session_via_cookie_or_api_key(
    org_id: uuid.UUID = Depends(get_org_id_via_cookie_or_api_key),
) -> AsyncGenerator[AsyncSession, None]:
    async for session in org_scoped_session(org_id):
        yield session


async def get_org_session(
    user: User = Depends(current_active_user),
) -> AsyncGenerator[AsyncSession, None]:
    """The session every org-scoped route (conversations, org membership)
    should depend on instead of get_db_session — opens one transaction for
    the request with `app.org_id` set to the current user's org (see
    db/session.py's org_scoped_session), so RLS applies.
    """
    async for session in org_scoped_session(user.org_id):
        yield session


def require_role(*allowed: UserRole) -> Callable[..., Coroutine[Any, Any, User]]:
    """Route dependency: 403s unless the current user's role is one of `allowed`.

    Layered on top of current_active_user (already active+verified) rather
    than replacing it — role is an authorization concern, not identity.
    """

    async def dependency(user: User = Depends(current_active_user)) -> User:
        if user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="insufficient role for this action"
            )
        return user

    return dependency

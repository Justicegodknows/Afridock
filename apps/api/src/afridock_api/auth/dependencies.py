import uuid
from collections.abc import AsyncGenerator, Callable, Coroutine
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi_users import FastAPIUsers
from sqlalchemy.ext.asyncio import AsyncSession

from afridock_api.auth.backend import auth_backend
from afridock_api.auth.manager import get_user_manager
from afridock_api.db.models.enums import UserRole
from afridock_api.db.models.user import User
from afridock_api.db.session import org_scoped_session

fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])

current_active_user = fastapi_users.current_user(active=True, verified=True)


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

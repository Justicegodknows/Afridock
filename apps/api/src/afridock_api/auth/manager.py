import uuid
from collections.abc import AsyncGenerator

import structlog
from fastapi import Depends, Request
from fastapi_users import BaseUserManager, UUIDIDMixin, exceptions
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from afridock_api.auth.schemas import UserCreate
from afridock_api.config import get_settings
from afridock_api.db.models.enums import UserRole
from afridock_api.db.models.organization import Organization
from afridock_api.db.models.user import User
from afridock_api.db.session import get_db_session

logger = structlog.get_logger()
settings = get_settings()

# E1's "weak password rejected" scenario: shorter than 12 characters.
MIN_PASSWORD_LENGTH = 12


async def get_user_db(
    session: AsyncSession = Depends(get_db_session),
) -> AsyncGenerator[SQLAlchemyUserDatabase[User, uuid.UUID], None]:
    yield SQLAlchemyUserDatabase(session, User)


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    # Local-dev fallback mirrors inference/credentials.py's pattern — every
    # deployed environment must still set API_SECRET_KEY explicitly.
    reset_password_token_secret = settings.api_secret_key
    verification_token_secret = settings.api_secret_key

    async def validate_password(  # type: ignore[override]
        self, password: str, user: UserCreate | User
    ) -> None:
        if len(password) < MIN_PASSWORD_LENGTH:
            raise exceptions.InvalidPasswordException(
                reason=f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
            )

    async def create(  # type: ignore[override]
        self,
        user_create: UserCreate,
        safe: bool = False,
        request: Request | None = None,
    ) -> User:
        """Overrides the base implementation to create a brand-new
        Organization alongside the user, making them its Admin — E1's
        "Successful signup" scenario. Only reached via the public
        /auth/register route (SignupPage); invited users are created
        directly by organizations.py with an org_id already known, never
        through this method.
        """
        await self.validate_password(user_create.password, user_create)

        existing_user = await self.user_db.get_by_email(user_create.email)
        if existing_user is not None:
            raise exceptions.UserAlreadyExists()

        session: AsyncSession = self.user_db.session  # type: ignore[attr-defined]
        organization = Organization(name=user_create.organization_name)
        session.add(organization)
        await session.flush()

        user_dict = (
            user_create.create_update_dict()  # type: ignore[no-untyped-call]
            if safe
            else user_create.create_update_dict_superuser()  # type: ignore[no-untyped-call]
        )
        user_dict.pop("organization_name", None)
        password = user_dict.pop("password")
        user_dict["hashed_password"] = self.password_helper.hash(password)
        user_dict["org_id"] = organization.id
        user_dict["role"] = UserRole.ADMIN

        created_user = await self.user_db.create(user_dict)
        await self.on_after_register(created_user, request)
        return created_user

    async def on_after_register(self, user: User, request: Request | None = None) -> None:
        # Triggers on_after_request_verify (below) with a fresh token — the
        # login route (auth/backend.py's requires_verification=True) then
        # rejects this user until that link is used, matching E1's "account
        # is inactive until the verification link is used".
        await self.request_verify(user, request)

    async def on_after_forgot_password(
        self, user: User, token: str, request: Request | None = None
    ) -> None:
        logger.info("auth.reset_password_link", user_id=str(user.id), token=token)

    async def on_after_request_verify(
        self, user: User, token: str, request: Request | None = None
    ) -> None:
        # No SMTP provider is in the stack yet (§2.1 of the plan) — logging
        # the link is the local-dev/self-hosted-friendly default until one
        # is added; swap this for a real email send without touching the
        # rest of the auth flow.
        logger.info("auth.verification_link", user_id=str(user.id), token=token)


async def get_user_manager(
    user_db: SQLAlchemyUserDatabase[User, uuid.UUID] = Depends(get_user_db),
) -> AsyncGenerator[UserManager, None]:
    yield UserManager(user_db)

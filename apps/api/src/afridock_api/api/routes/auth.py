from fastapi import APIRouter, Depends, HTTPException
from fastapi_users import exceptions
from fastapi_users.jwt import generate_jwt
from pydantic import BaseModel, EmailStr

from afridock_api.auth.backend import auth_backend
from afridock_api.auth.dependencies import fastapi_users
from afridock_api.auth.manager import UserManager, get_user_manager
from afridock_api.auth.schemas import UserCreate, UserRead, UserUpdate
from afridock_api.config import get_settings

router = APIRouter()

# Login/logout. requires_verification=True is what makes E1's "account is
# inactive until the verification link is used" scenario real — login
# 400s with LOGIN_USER_NOT_VERIFIED until the user follows that link.
router.include_router(
    fastapi_users.get_auth_router(auth_backend, requires_verification=True),
    prefix="/auth/cookie",
    tags=["auth"],
)
# POST /auth/register — the only route that reaches UserManager.create's
# organization-creation override (see auth/manager.py).
router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate), prefix="/auth", tags=["auth"]
)
# POST /auth/request-verify-token, POST /auth/verify
router.include_router(fastapi_users.get_verify_router(UserRead), prefix="/auth", tags=["auth"])
# POST /auth/forgot-password, POST /auth/reset-password — also backs the
# invite-completion flow (organizations.py reuses forgot_password()).
router.include_router(fastapi_users.get_reset_password_router(), prefix="/auth", tags=["auth"])
# GET/PATCH /users/me, GET/PATCH/DELETE /users/{id} (superuser-only by-id routes)
router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate), prefix="/users", tags=["users"]
)


class DevVerificationTokenRequest(BaseModel):
    email: EmailStr


class DevVerificationTokenResponse(BaseModel):
    token: str


@router.post(
    "/auth/dev/verification-token",
    response_model=DevVerificationTokenResponse,
    include_in_schema=False,
)
async def dev_verification_token(
    body: DevVerificationTokenRequest,
    user_manager: UserManager = Depends(get_user_manager),
) -> DevVerificationTokenResponse:
    """Local-dev-only convenience: mints a fresh verification token and
    returns it directly, so signing up in the browser doesn't require log
    access to the API server (see UserManager.on_after_request_verify — no
    SMTP provider exists yet). 404s outside API_ENV=local so this never
    exists in a real deployment; the token itself is byte-for-byte what
    `/auth/verify` already accepts, so this reuses that route rather than
    inventing a separate auto-verify path.
    """
    if get_settings().api_env != "local":
        raise HTTPException(status_code=404)

    try:
        user = await user_manager.get_by_email(body.email)
    except exceptions.UserNotExists:
        raise HTTPException(status_code=404, detail="user not found") from None

    if user.is_verified:
        raise HTTPException(status_code=400, detail="already verified")

    token = generate_jwt(
        {
            "sub": str(user.id),
            "email": user.email,
            "aud": user_manager.verification_token_audience,
        },
        user_manager.verification_token_secret,
        user_manager.verification_token_lifetime_seconds,
    )
    return DevVerificationTokenResponse(token=token)

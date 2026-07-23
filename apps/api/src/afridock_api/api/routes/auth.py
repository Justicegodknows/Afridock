from fastapi import APIRouter

from afridock_api.auth.backend import auth_backend
from afridock_api.auth.dependencies import fastapi_users
from afridock_api.auth.schemas import UserCreate, UserRead, UserUpdate

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

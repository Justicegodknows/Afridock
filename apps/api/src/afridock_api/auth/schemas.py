import uuid

from fastapi_users import schemas

from afridock_api.db.models.enums import UserRole


class UserRead(schemas.BaseUser[uuid.UUID]):
    org_id: uuid.UUID
    role: UserRole
    display_name: str | None = None


class UserCreate(schemas.BaseUserCreate):
    """`organization_name` only matters for the public /auth/register route
    (used by SignupPage) — see UserManager.create, which creates a brand
    new Organization and makes this user its Admin. Invited users never go
    through this schema/route; they're created directly by
    api/routes/organizations.py's invite endpoint with an org_id already
    known, then complete setup via the reset-password flow.
    """

    organization_name: str
    display_name: str | None = None


class UserUpdate(schemas.BaseUserUpdate):
    display_name: str | None = None

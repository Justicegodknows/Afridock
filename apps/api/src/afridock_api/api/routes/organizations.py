import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from afridock_api.auth.dependencies import (
    current_active_user,
    get_org_id_via_cookie_or_api_key,
    get_org_session,
    get_org_session_via_cookie_or_api_key,
    require_role,
)
from afridock_api.auth.manager import UserManager, get_user_manager
from afridock_api.db.models.enums import UserRole
from afridock_api.db.models.organization import Organization
from afridock_api.db.models.user import User

router = APIRouter(prefix="/organizations/current/members", tags=["organizations"])


class MemberOut(BaseModel):
    id: uuid.UUID
    email: str
    name: str | None
    role: UserRole
    status: str
    lastActiveAt: str | None


class InviteMembersRequest(BaseModel):
    emails: list[EmailStr]
    role: UserRole


class InviteMembersResponse(BaseModel):
    invited: list[str]


class UpdateRoleRequest(BaseModel):
    role: UserRole


def _to_member_out(user: User) -> MemberOut:
    return MemberOut(
        id=user.id,
        email=user.email,
        name=user.display_name,
        role=user.role,
        status="active" if user.is_verified else "pending",
        lastActiveAt=None,
    )


@router.get("", response_model=list[MemberOut])
async def list_members(
    org_id: uuid.UUID = Depends(get_org_id_via_cookie_or_api_key),
    session: AsyncSession = Depends(get_org_session_via_cookie_or_api_key),
) -> list[MemberOut]:
    """Reachable via cookie session (web app) or an org API key (plan E5's
    "a request is made with that key... authorized only for that key's
    organization" — see auth/dependencies.py). Every other route in this
    file stays cookie/Admin-only; this one is read-only and already
    org-scoped, so it's a safe first surface for machine access.
    """
    result = await session.execute(select(User).where(User.org_id == org_id))
    return [_to_member_out(user) for user in result.scalars().all()]


@router.post("/invite", response_model=InviteMembersResponse)
async def invite_members(
    body: InviteMembersRequest,
    admin: User = Depends(require_role(UserRole.ADMIN)),
    user_manager: UserManager = Depends(get_user_manager),
) -> InviteMembersResponse:
    """Creates each invited email as an already-active, already-verified
    user (trusted since an org Admin explicitly invited that exact
    address) with a random, unusable password, then reuses fastapi-users'
    forgot-password flow so they set a real one via the (logged, see
    UserManager.on_after_forgot_password) reset link — avoids building a
    bespoke invite-token system for what's functionally the same flow.
    """
    invited: list[str] = []
    for email in body.emails:
        existing = await user_manager.user_db.get_by_email(email)
        if existing is not None:
            continue
        # user_db.create() (not a raw session.add()+flush()) — it commits
        # internally, which raw ORM adds on this dependency's plain,
        # non-transaction-wrapped session (get_db_session) otherwise
        # wouldn't: nothing else here ever commits it, so the invited user
        # would silently roll back when the request ends.
        user = await user_manager.user_db.create(
            {
                "email": email,
                "hashed_password": user_manager.password_helper.hash(secrets.token_urlsafe(32)),
                "is_active": True,
                "is_verified": True,
                "org_id": admin.org_id,
                "role": body.role,
            }
        )
        await user_manager.forgot_password(user)
        invited.append(email)
    return InviteMembersResponse(invited=invited)


async def _get_member_or_404(
    session: AsyncSession, org_id: uuid.UUID, member_id: uuid.UUID
) -> User:
    # fastapi-users-db-sqlalchemy's TYPE_CHECKING stub types User.id as a
    # plain UUID at the class level (not a SQLAlchemy column expression), so
    # mypy sees `User.id == member_id` here as `bool`, not `ColumnElement`.
    result = await session.execute(
        select(User).where(User.id == member_id, User.org_id == org_id)  # type: ignore[arg-type]
    )
    member = result.scalar_one_or_none()
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="member not found")
    return member


@router.put("/{member_id}", response_model=MemberOut)
async def update_member_role(
    member_id: uuid.UUID,
    body: UpdateRoleRequest,
    admin: User = Depends(require_role(UserRole.ADMIN)),
    session: AsyncSession = Depends(get_org_session),
) -> MemberOut:
    member = await _get_member_or_404(session, admin.org_id, member_id)
    member.role = body.role
    await session.flush()
    return _to_member_out(member)


@router.delete("/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    member_id: uuid.UUID,
    admin: User = Depends(require_role(UserRole.ADMIN)),
    session: AsyncSession = Depends(get_org_session),
) -> None:
    if member_id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="cannot remove yourself"
        )
    member = await _get_member_or_404(session, admin.org_id, member_id)
    await session.delete(member)


settings_router = APIRouter(prefix="/organizations/current", tags=["organizations"])


class OrganizationOut(BaseModel):
    id: uuid.UUID
    name: str
    allowCommercialFallback: bool


class UpdateOrganizationSettingsRequest(BaseModel):
    allow_commercial_fallback: bool


@settings_router.get("", response_model=OrganizationOut)
async def get_current_organization(
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_org_session),
) -> OrganizationOut:
    org = await session.get(Organization, user.org_id)
    assert org is not None  # the authenticated user's own org always exists
    return OrganizationOut(
        id=org.id, name=org.name, allowCommercialFallback=org.allow_commercial_fallback
    )


@settings_router.patch("/settings", response_model=OrganizationOut)
async def update_current_organization_settings(
    body: UpdateOrganizationSettingsRequest,
    admin: User = Depends(require_role(UserRole.ADMIN)),
    session: AsyncSession = Depends(get_org_session),
) -> OrganizationOut:
    """Admin-only, deliberately: this is the org-level opt-in for real,
    non-zero-cost commercial inference (CLAUDE.md's #1 constraint) — the
    same trust boundary as billing settings, not a per-user preference.
    """
    org = await session.get(Organization, admin.org_id)
    assert org is not None
    org.allow_commercial_fallback = body.allow_commercial_fallback
    await session.flush()
    return OrganizationOut(
        id=org.id, name=org.name, allowCommercialFallback=org.allow_commercial_fallback
    )

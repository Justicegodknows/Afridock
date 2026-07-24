import csv
import io
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from afridock_api.auth.dependencies import current_active_user, get_org_session, require_role
from afridock_api.db.models.enums import UserRole
from afridock_api.db.models.provider import InferenceUsageLog
from afridock_api.db.models.user import User

router = APIRouter(prefix="/organizations/current", tags=["usage"])

_DEFAULT_AUDIT_LIMIT = 100


class UsageByProfile(BaseModel):
    modelProfile: str
    totalTokens: int
    costUsd: float
    requestCount: int


class UsageSummary(BaseModel):
    totalTokens: int
    totalCostUsd: float
    requestCount: int
    byProfile: list[UsageByProfile]


class AuditLogEntry(BaseModel):
    id: uuid.UUID
    userEmail: str | None
    modelProfile: str
    litellmModel: str
    promptTokens: int
    completionTokens: int
    totalTokens: int
    costUsd: float
    latencyMs: int | None
    status: str
    createdAt: str


@router.get("/usage", response_model=UsageSummary)
async def get_usage_summary(
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_org_session),
) -> UsageSummary:
    """Any active member can view — this is a cost dashboard, not the raw
    per-user audit trail (that's Admin-only, see get_audit_log below),
    matching the plan's "cost dashboard reflects near-real-time consumption"
    without a stated role restriction.
    """
    totals_result = await session.execute(
        select(
            func.coalesce(func.sum(InferenceUsageLog.total_tokens), 0),
            func.coalesce(func.sum(InferenceUsageLog.cost_usd), 0),
            func.count(InferenceUsageLog.id),
        ).where(InferenceUsageLog.org_id == user.org_id)
    )
    total_tokens, total_cost, request_count = totals_result.one()

    by_profile_result = await session.execute(
        select(
            InferenceUsageLog.model_profile,
            func.coalesce(func.sum(InferenceUsageLog.total_tokens), 0),
            func.coalesce(func.sum(InferenceUsageLog.cost_usd), 0),
            func.count(InferenceUsageLog.id),
        )
        .where(InferenceUsageLog.org_id == user.org_id)
        .group_by(InferenceUsageLog.model_profile)
        .order_by(func.sum(InferenceUsageLog.total_tokens).desc())
    )
    by_profile = [
        UsageByProfile(
            modelProfile=profile, totalTokens=tokens, costUsd=float(cost), requestCount=count
        )
        for profile, tokens, cost, count in by_profile_result.all()
    ]

    return UsageSummary(
        totalTokens=total_tokens,
        totalCostUsd=float(total_cost),
        requestCount=request_count,
        byProfile=by_profile,
    )


async def _fetch_audit_rows(
    session: AsyncSession,
    org_id: uuid.UUID,
    since: datetime | None,
    until: datetime | None,
    limit: int | None,
) -> list[tuple[InferenceUsageLog, str | None]]:
    stmt = (
        select(InferenceUsageLog, User.email)  # type: ignore[call-overload]
        .outerjoin(User, User.id == InferenceUsageLog.user_id)
        .where(InferenceUsageLog.org_id == org_id)
        .order_by(InferenceUsageLog.created_at.desc())
    )
    if since is not None:
        stmt = stmt.where(InferenceUsageLog.created_at >= since)
    if until is not None:
        stmt = stmt.where(InferenceUsageLog.created_at <= until)
    if limit is not None:
        stmt = stmt.limit(limit)
    result = await session.execute(stmt)
    return [(log, email) for log, email in result.all()]


def _to_audit_entry(log: InferenceUsageLog, email: str | None) -> AuditLogEntry:
    return AuditLogEntry(
        id=log.id,
        userEmail=email,
        modelProfile=log.model_profile,
        litellmModel=log.litellm_model,
        promptTokens=log.prompt_tokens,
        completionTokens=log.completion_tokens,
        totalTokens=log.total_tokens,
        costUsd=float(log.cost_usd),
        latencyMs=log.latency_ms,
        status=log.status,
        createdAt=log.created_at.isoformat(),
    )


@router.get("/audit", response_model=list[AuditLogEntry])
async def get_audit_log(
    since: datetime | None = Query(default=None),
    until: datetime | None = Query(default=None),
    admin: User = Depends(require_role(UserRole.ADMIN)),
    session: AsyncSession = Depends(get_org_session),
) -> list[AuditLogEntry]:
    """Admin-only — matches the plan's "Viewers cannot access the audit
    export" (and, more strictly here, Users can't either: this is the raw
    per-user trail, not the aggregate dashboard above)."""
    rows = await _fetch_audit_rows(session, admin.org_id, since, until, _DEFAULT_AUDIT_LIMIT)
    return [_to_audit_entry(log, email) for log, email in rows]


@router.get("/audit/export.csv")
async def export_audit_log_csv(
    since: datetime | None = Query(default=None),
    until: datetime | None = Query(default=None),
    admin: User = Depends(require_role(UserRole.ADMIN)),
    session: AsyncSession = Depends(get_org_session),
) -> StreamingResponse:
    rows = await _fetch_audit_rows(session, admin.org_id, since, until, None)

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "id",
            "user_email",
            "model_profile",
            "litellm_model",
            "prompt_tokens",
            "completion_tokens",
            "total_tokens",
            "cost_usd",
            "latency_ms",
            "status",
            "created_at",
        ]
    )
    for log, email in rows:
        writer.writerow(
            [
                log.id,
                email or "",
                log.model_profile,
                log.litellm_model,
                log.prompt_tokens,
                log.completion_tokens,
                log.total_tokens,
                log.cost_usd,
                log.latency_ms if log.latency_ms is not None else "",
                log.status,
                log.created_at.isoformat(),
            ]
        )
    buffer.seek(0)

    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=audit-log.csv"},
    )

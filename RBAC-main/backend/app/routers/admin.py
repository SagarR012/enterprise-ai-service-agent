"""Admin endpoints — audit logs, stats dashboard."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.services.auth_service import get_current_user
from app.services.audit_service import get_all_logs, get_logs_for_user, get_admin_stats
from app.schemas.audit import AuditLogOut, AdminStats

router = APIRouter(prefix="/api/admin", tags=["admin"])


def _require_admin(user: User):
    if user.role not in ("exec_admin", "legal_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")


@router.get("/stats", response_model=AdminStats)
def admin_stats(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get dashboard statistics. Admin-only."""
    _require_admin(user)
    stats = get_admin_stats(db)
    return AdminStats(
        total_queries=stats["total_queries"],
        pii_redacted_count=stats["pii_redacted_count"],
        rbac_blocked_count=stats["rbac_blocked_count"],
        documents_indexed=stats["documents_indexed"],
        total_chunks=stats["total_chunks"],
        recent_logs=[
            AuditLogOut(
                id=log.id,
                user_id=log.user_id,
                query_text=log.query_text,
                chunks_retrieved=log.chunks_retrieved,
                pii_masked=log.pii_masked,
                rbac_blocked=log.rbac_blocked,
                role_used=log.role_used,
                timestamp=log.timestamp.isoformat(),
            )
            for log in stats["recent_logs"]
        ],
    )


@router.get("/audit-logs")
def audit_logs(
    limit: int = 50,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get audit logs. Admins see all; regular users see only their own."""
    _require_admin(user)
    logs = get_all_logs(db, limit=limit)
    return [
        AuditLogOut(
            id=log.id,
            user_id=log.user_id,
            query_text=log.query_text,
            chunks_retrieved=log.chunks_retrieved,
            pii_masked=log.pii_masked,
            rbac_blocked=log.rbac_blocked,
            role_used=log.role_used,
            timestamp=log.timestamp.isoformat(),
        )
        for log in logs
    ]

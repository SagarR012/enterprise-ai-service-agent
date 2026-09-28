"""Audit logging — records every RAG query for compliance."""
from typing import List

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def log_query(
    db: Session,
    user_id: str,
    query_text: str,
    chunks_retrieved: List[str],
    pii_masked: bool,
    rbac_blocked: bool,
    role_used: str,
) -> AuditLog:
    entry = AuditLog(
        user_id=user_id,
        query_text=query_text,
        chunks_retrieved=chunks_retrieved,
        pii_masked=pii_masked,
        rbac_blocked=rbac_blocked,
        role_used=role_used,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def get_logs_for_user(db: Session, user_id: str, limit: int = 50) -> List[AuditLog]:
    return (
        db.query(AuditLog)
        .filter(AuditLog.user_id == user_id)
        .order_by(AuditLog.timestamp.desc())
        .limit(limit)
        .all()
    )


def get_all_logs(db: Session, limit: int = 100) -> List[AuditLog]:
    return (
        db.query(AuditLog)
        .order_by(AuditLog.timestamp.desc())
        .limit(limit)
        .all()
    )


def get_admin_stats(db: Session) -> dict:
    from app.models.document import Document, DocumentChunk

    total_queries = db.query(AuditLog).count()
    pii_redacted = db.query(AuditLog).filter(AuditLog.pii_masked == True).count()
    rbac_blocked = db.query(AuditLog).filter(AuditLog.rbac_blocked == True).count()
    docs_indexed = db.query(Document).count()
    total_chunks = db.query(DocumentChunk).count()
    recent = get_all_logs(db, limit=20)

    return {
        "total_queries": total_queries,
        "pii_redacted_count": pii_redacted,
        "rbac_blocked_count": rbac_blocked,
        "documents_indexed": docs_indexed,
        "total_chunks": total_chunks,
        "recent_logs": recent,
    }

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, Boolean, Text, Integer, func
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AuditLog(Base):
    """Immutable audit trail — every RAG query writes a row here."""
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    query_text: Mapped[str] = mapped_column(Text)
    chunks_retrieved: Mapped[dict] = mapped_column(JSON, default=list)
    pii_masked: Mapped[bool] = mapped_column(Boolean, default=False)
    rbac_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    role_used: Mapped[str] = mapped_column(String(50))
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

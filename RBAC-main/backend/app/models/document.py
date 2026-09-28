import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, ForeignKey, Boolean, Text, func
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    workspace_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workspaces.id")
    )
    filename: Mapped[str] = mapped_column(String(500))
    uploader_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id")
    )
    sensitivity_level: Mapped[str] = mapped_column(
        String(20), default="internal"
    )  # public | internal | confidential | restricted
    upload_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    workspace = relationship("Workspace", back_populates="documents")
    uploader = relationship("User", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    """Each row stores both raw and PII-masked text.
    embedding_id links to the Qdrant point so we can update/delete vector + DB in sync."""
    __tablename__ = "document_chunks"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("documents.id", ondelete="CASCADE")
    )
    embedding_id: Mapped[str] = mapped_column(String(36), index=True)  # Qdrant point UUID
    access_roles: Mapped[dict] = mapped_column(JSON)  # {"roles": ["exec_admin", "legal_admin"]}
    raw_text: Mapped[str] = mapped_column(Text)
    masked_text: Mapped[str] = mapped_column(Text)
    contains_pii: Mapped[bool] = mapped_column(Boolean, default=False)

    document = relationship("Document", back_populates="chunks")

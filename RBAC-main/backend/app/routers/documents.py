"""Document management endpoints — upload, list, delete."""
import io
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.document import Document
from app.services.auth_service import get_current_user
from app.services.document_service import (
    extract_text,
    chunk_text,
    create_document_record,
    create_chunk_records,
    delete_document_cascade,
    list_documents_for_workspace,
    list_all_documents,
)
from app.services.pii_service import mask_chunks
from app.services.embedding_service import upsert_chunks, delete_by_document_id
from app.schemas.document import DocumentOut, DocumentUploadResponse, DocumentListResponse

router = APIRouter(prefix="/api/documents", tags=["documents"])

SENSITIVITY_LEVELS = {"public", "internal", "confidential", "restricted"}


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    sensitivity_level: str = Form("internal"),
    workspace_id: str | None = Form(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload a document (.txt or .pdf). Extracts text, chunks it, masks PII, embeds, and stores."""
    if sensitivity_level not in SENSITIVITY_LEVELS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sensitivity_level. Must be one of: {SENSITIVITY_LEVELS}",
        )

    # Use user's workspace if not specified
    ws_id = workspace_id or user.workspace_id

    # Only exec_admin and legal_admin can set restricted/confidential
    if sensitivity_level in ("confidential", "restricted") and user.role not in ("exec_admin", "legal_admin"):
        raise HTTPException(
            status_code=403,
            detail="Only exec_admin and legal_admin can upload confidential/restricted documents",
        )

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")

    # 1. Extract text
    raw_text = extract_text(file.filename, content)
    if not raw_text.strip():
        raise HTTPException(status_code=400, detail="No text content found in file")

    # 2. Chunk
    chunks = chunk_text(raw_text)
    if not chunks:
        raise HTTPException(status_code=400, detail="Document produced no chunks after processing")

    # 3. PII mask
    masked = mask_chunks(chunks)

    # 4. Create document record
    doc = create_document_record(db, ws_id, user.id, file.filename, sensitivity_level)

    # 5. Create chunk records in DB (need IDs for Qdrant payload)
    # Temporarily assign IDs for embedding linkage
    chunk_records = []
    for raw, msk in zip(chunks, masked):
        from app.models.document import DocumentChunk
        import uuid as _uuid
        chunk = DocumentChunk(
            document_id=doc.id,
            embedding_id="pending",
            access_roles={"roles": [user.role]},
            raw_text=raw,
            masked_text=msk,
            contains_pii=(raw != msk),
        )
        db.add(chunk)
        db.flush()
        chunk_records.append(chunk)

    # 6. Embed and upsert to Qdrant
    try:
        embedding_ids = upsert_chunks(
            chunk_texts=[c.raw_text for c in chunk_records],
            access_roles=[user.role],
            document_id=doc.id,
            chunk_db_ids=[c.id for c in chunk_records],
        )
        # Update chunk records with real embedding IDs
        for chunk, emb_id in zip(chunk_records, embedding_ids):
            chunk.embedding_id = emb_id
    except Exception as e:
        # Rollback DB changes if embedding fails
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to embed document: {str(e)}",
        )

    db.commit()

    pii_detected = any(c.contains_pii for c in chunk_records)

    return DocumentUploadResponse(
        document_id=doc.id,
        filename=doc.filename,
        chunks_created=len(chunk_records),
        pii_detected=pii_detected,
        sensitivity_level=doc.sensitivity_level,
    )


@router.get("/", response_model=DocumentListResponse)
def list_documents(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all documents in the user's workspace."""
    docs = list_documents_for_workspace(db, user.workspace_id)
    result = []
    for d in docs:
        result.append(
            DocumentOut(
                id=d.id,
                filename=d.filename,
                workspace_id=d.workspace_id,
                uploader_id=d.uploader_id,
                sensitivity_level=d.sensitivity_level,
                upload_date=d.upload_date,
                chunk_count=len(d.chunks),
            )
        )
    return DocumentListResponse(documents=result, total=len(result))


@router.delete("/{document_id}")
def delete_document(
    document_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a document and its chunks from both Postgres and Qdrant."""
    from app.models.document import Document

    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Only the uploader or exec_admin can delete
    if doc.uploader_id != user.id and user.role != "exec_admin":
        raise HTTPException(status_code=403, detail="Not authorized to delete this document")

    embedding_ids = delete_document_cascade(db, document_id)
    try:
        delete_by_document_id(document_id)
    except Exception:
        pass  # Best-effort Qdrant cleanup

    db.commit()
    return {"detail": "Document deleted", "chunks_removed": len(embedding_ids)}

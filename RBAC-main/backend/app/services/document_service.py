"""Document ingestion: text extraction, chunking, PII masking, and Qdrant embedding."""
import uuid
import re
from typing import List, Tuple

from sqlalchemy.orm import Session

from app.models.document import Document, DocumentChunk


# ── Text Extraction ──────────────────────────────────────────────────

def extract_text_from_txt(content: bytes) -> str:
    return content.decode("utf-8", errors="replace")


def extract_text_from_pdf(content: bytes) -> str:
    from pypdf import PdfReader
    import io
    reader = PdfReader(io.BytesIO(content))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n\n".join(pages)


def extract_text(filename: str, content: bytes) -> str:
    """Dispatch to the right extractor based on file extension."""
    lower = filename.lower()
    if lower.endswith(".txt"):
        return extract_text_from_txt(content)
    if lower.endswith(".pdf"):
        return extract_text_from_pdf(content)
    # Fallback: treat as plain text
    return extract_text_from_txt(content)


# ── Chunking ─────────────────────────────────────────────────────────

def chunk_text(text: str, max_chars: int = 1000, overlap: int = 200) -> List[str]:
    """Split text into overlapping chunks at paragraph or sentence boundaries."""
    if not text.strip():
        return []

    paragraphs = re.split(r"\n\s*\n", text)
    chunks: List[str] = []
    current = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        if len(current) + len(para) + 2 <= max_chars:
            current = f"{current}\n\n{para}" if current else para
        else:
            if current:
                chunks.append(current)
            # If a single paragraph exceeds max_chars, split by sentences
            if len(para) > max_chars:
                sentences = re.split(r"(?<=[.!?])\s+", para)
                current = ""
                for sent in sentences:
                    if len(current) + len(sent) + 1 <= max_chars:
                        current = f"{current} {sent}" if current else sent
                    else:
                        if current:
                            chunks.append(current)
                        current = sent
            else:
                current = para

    if current:
        chunks.append(current)

    # Apply overlap: prepend tail of previous chunk
    if overlap > 0 and len(chunks) > 1:
        overlapped = [chunks[0]]
        for i in range(1, len(chunks)):
            prev = chunks[i - 1]
            tail = prev[-overlap:] if len(prev) > overlap else prev
            # Find a clean sentence boundary in the tail
            space_idx = tail.find(" ")
            if space_idx > 0:
                tail = tail[space_idx + 1:]
            overlapped.append(f"{tail}\n\n{chunks[i]}" if tail else chunks[i])
        chunks = overlapped

    return chunks


# ── Database Operations ──────────────────────────────────────────────

def create_document_record(
    db: Session,
    workspace_id: str,
    uploader_id: str,
    filename: str,
    sensitivity_level: str = "internal",
) -> Document:
    doc = Document(
        workspace_id=workspace_id,
        uploader_id=uploader_id,
        filename=filename,
        sensitivity_level=sensitivity_level,
    )
    db.add(doc)
    db.flush()
    return doc


def create_chunk_records(
    db: Session,
    document_id: str,
    chunks: List[str],
    masked_chunks: List[str],
    access_roles: List[str],
    embedding_ids: List[str],
) -> List[DocumentChunk]:
    """Persist chunk metadata in Postgres after embedding."""
    records: List[DocumentChunk] = []
    for raw, masked, emb_id in zip(chunks, masked_chunks, embedding_ids):
        chunk = DocumentChunk(
            document_id=document_id,
            embedding_id=emb_id,
            access_roles={"roles": access_roles},
            raw_text=raw,
            masked_text=masked,
            contains_pii=(raw != masked),
        )
        db.add(chunk)
        records.append(chunk)
    db.flush()
    return records


def get_document_with_chunks(db: Session, document_id: str) -> Document | None:
    return db.query(Document).filter(Document.id == document_id).first()


def delete_document_cascade(db: Session, document_id: str) -> List[str]:
    """Delete document + chunks. Returns list of embedding_ids for Qdrant cleanup."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        return []
    embedding_ids = [c.embedding_id for c in doc.chunks]
    db.delete(doc)
    db.flush()
    return embedding_ids


def list_documents_for_workspace(db: Session, workspace_id: str) -> List[Document]:
    return (
        db.query(Document)
        .filter(Document.workspace_id == workspace_id)
        .order_by(Document.upload_date.desc())
        .all()
    )


def list_all_documents(db: Session) -> List[Document]:
    return db.query(Document).order_by(Document.upload_date.desc()).all()

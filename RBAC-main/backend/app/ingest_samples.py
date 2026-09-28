"""Ingest sample documents from data/ into the system.
Usage: python -m app.ingest_samples   (from inside the backend/ directory)
Requires: PostgreSQL and Qdrant running, Gemini API key set."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal, Base
from app.models import User, Workspace
from app.services.document_service import extract_text, chunk_text, create_document_record
from app.services.pii_service import mask_chunks
from app.services.embedding_service import upsert_chunks, ensure_collection
from app.models.document import DocumentChunk

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

# Maps workspace name to the documents that belong there
DOC_WORKSPACE_MAP = {
    "executive": ["executive_q2_review.txt"],
    "legal": ["legal_contract_acme.txt"],
    "finance": ["finance_q2_report.txt"],
    "general": ["general_handbook.txt"],
}


def ingest():
    from app.database import engine
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Build workspace lookup
        ws_map = {}
        for ws in db.query(Workspace).all():
            ws_map[ws.name] = ws.id

        # Find demo users for uploader_id
        users = {u.role: u for u in db.query(User).all()}

        # Map workspace → role (for access_roles)
        ws_role_map = {
            "executive": "exec_admin",
            "legal": "legal_admin",
            "finance": "finance_viewer",
            "general": "general_viewer",
        }

        # Ensure Qdrant collection exists
        ensure_collection()

        for ws_name, filenames in DOC_WORKSPACE_MAP.items():
            for fname in filenames:
                fpath = DATA_DIR / fname
                if not fpath.exists():
                    print(f"  ✗ File not found: {fpath}")
                    continue

                content = fpath.read_bytes()
                raw_text = extract_text(fname, content)
                chunks = chunk_text(raw_text)
                masked = mask_chunks(chunks)

                ws_id = ws_map.get(ws_name)
                role = ws_role_map.get(ws_name, "general_viewer")
                uploader = users.get(role)

                if not ws_id or not uploader:
                    print(f"  ✗ Missing workspace or user for {ws_name}")
                    continue

                doc = create_document_record(db, ws_id, uploader.id, fname, "internal")
                db.flush()

                chunk_records = []
                for raw, msk in zip(chunks, masked):
                    chunk = DocumentChunk(
                        document_id=doc.id,
                        embedding_id="pending",
                        access_roles={"roles": [role]},
                        raw_text=raw,
                        masked_text=msk,
                        contains_pii=(raw != msk),
                    )
                    db.add(chunk)
                    db.flush()
                    chunk_records.append(chunk)

                try:
                    embedding_ids = upsert_chunks(
                        chunk_texts=[c.raw_text for c in chunk_records],
                        access_roles=[role],
                        document_id=doc.id,
                        chunk_db_ids=[c.id for c in chunk_records],
                    )
                    for chunk, emb_id in zip(chunk_records, embedding_ids):
                        chunk.embedding_id = emb_id
                    db.commit()
                    print(f"  ✓ Ingested {fname} → {len(chunks)} chunks (workspace: {ws_name})")
                except Exception as e:
                    db.rollback()
                    print(f"  ✗ Failed to embed {fname}: {e}")

        print("\nIngestion complete.")
    finally:
        db.close()


if __name__ == "__main__":
    ingest()

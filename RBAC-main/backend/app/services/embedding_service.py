"""Qdrant vector database integration for document chunk embeddings."""
import uuid
from typing import List, Optional

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)

from app.config import QDRANT_HOST, QDRANT_PORT, QDRANT_COLLECTION

_client: Optional[QdrantClient] = None

# Embedding dimension for Google Gemini gemini-embedding-001
EMBEDDING_DIM = 3072


def get_client() -> QdrantClient:
    global _client
    if _client is None:
        _client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    return _client


def ensure_collection():
    """Create the collection if it doesn't exist, or recreate if dimension mismatch."""
    client = get_client()
    collections = [c.name for c in client.get_collections().collections]
    if QDRANT_COLLECTION in collections:
        info = client.get_collection(QDRANT_COLLECTION)
        if info.config.params.vectors.size != EMBEDDING_DIM:
            client.delete_collection(QDRANT_COLLECTION)
        else:
            return
    client.create_collection(
        collection_name=QDRANT_COLLECTION,
        vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
    )


def get_embeddings(texts: List[str]) -> List[List[float]]:
    """Get embeddings from Google Gemini API."""
    import google.generativeai as genai
    from app.config import GEMINI_API_KEY

    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set. Add it to .env")

    genai.configure(api_key=GEMINI_API_KEY)
    result = genai.embed_content(
        model="models/gemini-embedding-001",
        content=texts,
        task_type="retrieval_document",
    )
    return result["embedding"]


def upsert_chunks(
    chunk_texts: List[str],
    access_roles: List[str],
    document_id: str,
    chunk_db_ids: List[str],
) -> List[str]:
    """Embed chunks and upsert into Qdrant. Returns embedding_ids (point UUIDs)."""
    ensure_collection()
    client = get_client()
    embeddings = get_embeddings(chunk_texts)

    points = []
    embedding_ids = []
    for i, (emb, text, db_id) in enumerate(zip(embeddings, chunk_texts, chunk_db_ids)):
        point_id = str(uuid.uuid4())
        embedding_ids.append(point_id)
        points.append(
            PointStruct(
                id=point_id,
                vector=emb,
                payload={
                    "text": text,
                    "document_id": document_id,
                    "chunk_db_id": db_id,
                    "access_roles": access_roles,
                    "index": i,
                },
            )
        )

    client.upsert(collection_name=QDRANT_COLLECTION, points=points)
    return embedding_ids


def search_chunks(
    query_embedding: List[float],
    user_roles: List[str],
    top_k: int = 5,
) -> List[dict]:
    """Search Qdrant with RBAC filtering. Only returns chunks the user's role can access."""
    client = get_client()
    ensure_collection()

    # Build a filter: access_roles must contain at least one of the user's roles
    must_conditions = [
        FieldCondition(key="access_roles", match=MatchValue(value=role))
        for role in user_roles
    ]

    results = client.search(
        collection_name=QDRANT_COLLECTION,
        query_vector=query_embedding,
        query_filter=Filter(should=must_conditions) if must_conditions else None,
        limit=top_k,
        with_payload=True,
    )

    return [
        {
            "id": hit.id,
            "score": hit.score,
            "payload": hit.payload,
        }
        for hit in results
    ]


def delete_by_document_id(document_id: str):
    """Delete all vectors for a given document."""
    client = get_client()
    ensure_collection()
    client.delete(
        collection_name=QDRANT_COLLECTION,
        points_selector=Filter(
            must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))]
        ),
    )

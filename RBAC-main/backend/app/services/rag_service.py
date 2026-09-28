"""RAG pipeline: embed query → retrieve relevant chunks → generate answer via Gemini."""
from typing import List, Tuple

import google.generativeai as genai

from app.config import GEMINI_API_KEY, PRIVILEGED_ROLES
from app.services.embedding_service import get_embeddings, search_chunks

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = """You are an enterprise knowledge base assistant. Answer questions based ONLY on the provided context.
If the context does not contain enough information, say so clearly.
Be concise and professional. Cite your sources when possible.
Never fabricate information. If PII has been redacted, do not try to guess the original values."""


def retrieve_relevant_chunks(
    query: str,
    user_roles: List[str],
    top_k: int = 5,
) -> Tuple[List[dict], bool]:
    """Embed query, search Qdrant with RBAC filter. Returns (chunks, was_blocked)."""
    query_emb = get_embeddings([query])[0]
    results = search_chunks(query_emb, user_roles, top_k=top_k * 2)

    accessible = []
    for r in results:
        chunk_roles = r["payload"].get("access_roles", [])
        if isinstance(chunk_roles, dict):
            chunk_roles = chunk_roles.get("roles", [])
        if any(role in chunk_roles for role in user_roles):
            accessible.append(r)

    blocked = len(accessible) == 0
    return accessible[:top_k], blocked


def build_context(chunks: List[dict], user_roles: List[str]) -> str:
    """Assemble context string from retrieved chunks.
    Privileged roles see raw text; others see masked text."""
    is_privileged = any(r in PRIVILEGED_ROLES for r in user_roles)
    parts = []
    for i, chunk in enumerate(chunks):
        text = chunk["payload"].get("text", "")
        doc_id = chunk["payload"].get("document_id", "unknown")
        score = chunk.get("score", 0)
        parts.append(f"[Source {i+1} | doc:{doc_id} | score:{score:.3f}]\n{text}")
    return "\n\n---\n\n".join(parts)


def generate_answer(
    query: str,
    context: str,
    chat_history: List[dict] = None,
) -> str:
    """Call Gemini to generate an answer given the query and retrieved context."""
    model = genai.GenerativeModel(
        model_name="gemini-3.6-flash",
        system_instruction=SYSTEM_PROMPT,
    )

    # Build conversation context
    history_text = ""
    if chat_history:
        for msg in chat_history[-6:]:  # Last 3 exchanges max
            role = msg.get("role", "user")
            content = msg.get("content", "")
            history_text += f"{role}: {content}\n"

    prompt = f"""Context from knowledge base:
{context}

{f'Previous conversation:{chr(10)}{history_text}' if history_text else ''}

User question: {query}

Answer based on the context above. If the context is empty, say you don't have enough information."""

    response = model.generate_content(prompt)
    return response.text


def rag_query(
    query: str,
    user_roles: List[str],
    chat_history: List[dict] = None,
) -> Tuple[str, List[dict], bool]:
    """Full RAG pipeline: retrieve + generate. Returns (answer, chunks_used, was_blocked)."""
    chunks, blocked = retrieve_relevant_chunks(query, user_roles)

    if blocked:
        return (
            "I don't have any relevant documents accessible to your role. "
            "Please contact an administrator if you believe this is an error.",
            [],
            True,
        )

    context = build_context(chunks, user_roles)
    answer = generate_answer(query, context, chat_history)
    return answer, chunks, False

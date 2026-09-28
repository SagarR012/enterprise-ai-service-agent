"""Chat / RAG query endpoint."""
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.conversation import Conversation, Message
from app.services.auth_service import get_current_user
from app.services.rag_service import rag_query
from app.services.audit_service import log_query
from app.services.pii_service import detect_pii
from app.schemas.chat import ChatRequest, ChatResponse, Citation, FeedbackRequest
from app.services.feedback_service import record_feedback

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
def chat(
    body: ChatRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Send a message and get a RAG-powered answer."""
    user_roles = [user.role]

    # Get or create conversation
    conversation = None
    if body.conversation_id:
        conversation = (
            db.query(Conversation)
            .filter(
                Conversation.id == body.conversation_id,
                Conversation.user_id == user.id,
            )
            .first()
        )
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conversation = Conversation(user_id=user.id)
        db.add(conversation)
        db.flush()

    # Save user message
    user_msg = Message(
        conversation_id=conversation.id,
        role="user",
        content=body.message,
        cited_chunks=[],
    )
    db.add(user_msg)
    db.flush()

    # Build chat history from conversation
    history = (
        db.query(Message)
        .filter(Message.conversation_id == conversation.id)
        .order_by(Message.created_at)
        .all()
    )
    chat_history = [{"role": m.role, "content": m.content} for m in history[:-1]]

    # Run RAG pipeline
    try:
        answer, chunks, rbac_blocked = rag_query(
            query=body.message,
            user_roles=user_roles,
            chat_history=chat_history,
        )
    except Exception as e:
        answer = f"Sorry, I encountered an error processing your query: {str(e)}"
        chunks = []
        rbac_blocked = False

    # Check for PII in the answer
    pii_in_answer = detect_pii(answer)
    pii_masked = len(pii_in_answer) > 0

    # Build citations
    citations = [
        Citation(
            chunk_id=chunk["payload"].get("chunk_db_id", chunk["id"]),
            source_name=chunk["payload"].get("document_id", "unknown"),
            relevance_score=chunk.get("score", 0),
        )
        for chunk in chunks
    ]

    # Save assistant message
    assistant_msg = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=answer,
        cited_chunks=[c.model_dump() for c in citations],
    )
    db.add(assistant_msg)
    db.flush()

    # Audit log
    log_query(
        db=db,
        user_id=user.id,
        query_text=body.message,
        chunks_retrieved=[c.model_dump() for c in citations],
        pii_masked=pii_masked,
        rbac_blocked=rbac_blocked,
        role_used=user.role,
    )

    db.commit()

    return ChatResponse(
        answer=answer,
        citations=citations,
        pii_masked=pii_masked,
        rbac_blocked=rbac_blocked,
        conversation_id=conversation.id,
        withheld_notice="Some results may have been restricted based on your role."
            if rbac_blocked else None,
    )


@router.post("/feedback")
def submit_feedback(
    body: FeedbackRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit thumbs up/down feedback on an assistant response."""
    msg = db.query(Message).filter(Message.id == body.message_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    record_feedback(
        db=db,
        message_id=body.message_id,
        user_id=user.id,
        rating=body.rating,
        comment=body.comment,
    )
    return {"detail": "Feedback recorded"}


@router.get("/conversations")
def list_conversations(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all conversations for the current user."""
    convos = (
        db.query(Conversation)
        .filter(Conversation.user_id == user.id)
        .order_by(Conversation.created_at.desc())
        .all()
    )
    return [
        {
            "id": c.id,
            "created_at": c.created_at.isoformat(),
            "message_count": len(c.messages),
        }
        for c in convos
    ]


@router.get("/conversations/{conversation_id}")
def get_conversation(
    conversation_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get full message history for a conversation."""
    conv = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user.id,
        )
        .first()
    )
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conv.id)
        .order_by(Message.created_at)
        .all()
    )
    return {
        "id": conv.id,
        "created_at": conv.created_at.isoformat(),
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "cited_chunks": m.cited_chunks,
                "created_at": m.created_at.isoformat(),
            }
            for m in messages
        ],
    }

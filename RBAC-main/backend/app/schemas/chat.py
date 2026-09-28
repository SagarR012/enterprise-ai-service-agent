from pydantic import BaseModel
from typing import List, Optional


class Citation(BaseModel):
    chunk_id: str
    source_name: str
    relevance_score: float


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    citations: List[Citation]
    pii_masked: bool
    rbac_blocked: bool
    conversation_id: str
    withheld_notice: Optional[str] = None


class FeedbackRequest(BaseModel):
    message_id: str
    rating: int  # 1 or -1
    comment: Optional[str] = None

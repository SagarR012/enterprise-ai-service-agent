from pydantic import BaseModel
from typing import List, Optional


class AuditLogOut(BaseModel):
    id: str
    user_id: str
    query_text: str
    chunks_retrieved: list
    pii_masked: bool
    rbac_blocked: bool
    role_used: str
    timestamp: str

    class Config:
        from_attributes = True


class AdminStats(BaseModel):
    total_queries: int
    pii_redacted_count: int
    rbac_blocked_count: int
    documents_indexed: int
    total_chunks: int
    recent_logs: List[AuditLogOut]

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class DocumentOut(BaseModel):
    id: str
    filename: str
    workspace_id: str
    uploader_id: str
    sensitivity_level: str
    upload_date: datetime
    chunk_count: int = 0

    class Config:
        from_attributes = True


class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    chunks_created: int
    pii_detected: bool
    sensitivity_level: str


class DocumentListResponse(BaseModel):
    documents: List[DocumentOut]
    total: int

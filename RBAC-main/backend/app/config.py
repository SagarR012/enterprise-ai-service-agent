"""Centralised config — reads .env once at import time."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://kbadmin:kbpass123@localhost:5432/knowledge_base")
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "doc_chunks")

JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-demo-key-change-in-prod")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRY_MINUTES = int(os.getenv("JWT_EXPIRY_MINUTES", "120"))

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Roles that see raw PII text during retrieval (Checkpoint 2)
PRIVILEGED_ROLES = [r.strip() for r in os.getenv("PII_PRIVILEGED_ROLES", "exec_admin,legal_admin").split(",")]

# Allowed roles in the system
VALID_ROLES = {"exec_admin", "legal_admin", "finance_viewer", "general_viewer"}

# Workspace names
WORKSPACES = ["executive", "legal", "finance", "general"]

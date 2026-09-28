"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.routers import auth, demo, documents, chat, admin

# Create all tables on startup (for MVP — production would use Alembic migrations)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Enterprise Knowledge Base & RAG Assistant",
    description="RBAC-enforced RAG with PII guardrails — college major project",
    version="0.2.0",
)

# Allow the React dev server to talk to the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(demo.router)
app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(admin.router)

# Future routers (will add in later phases):
# app.include_router(frontend.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "kb-rag-backend"}

"""Seed script — run once after `init_db` to populate workspaces & demo users.
Usage:  python -m app.seed   (from inside the backend/ directory)"""
import sys
from pathlib import Path

# Ensure `backend/` is on sys.path so `app.*` resolves
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import engine, SessionLocal, Base
from app.models import User, Workspace
from app.services.auth_service import hash_password
from app.config import WORKSPACES


SEED_USERS = [
    # Each demo user maps to one role and one primary workspace
    {"name": "Alice Executive",  "email": "alice@enron.com", "password": "password", "role": "exec_admin",      "ws": "executive"},
    {"name": "David Legal",      "email": "david@enron.com", "password": "password", "role": "legal_admin",      "ws": "legal"},
    {"name": "Priya Finance",    "email": "priya@enron.com", "password": "password", "role": "finance_viewer",   "ws": "finance"},
    {"name": "Karen General",    "email": "karen@enron.com", "password": "password", "role": "general_viewer",   "ws": "general"},
]


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # ── Workspaces ──────────────────────────────────────────────
        ws_map = {}
        for name in WORKSPACES:
            ws = db.query(Workspace).filter(Workspace.name == name).first()
            if not ws:
                ws = Workspace(name=name)
                db.add(ws)
                db.flush()
            ws_map[name] = ws.id

        # ── Users ───────────────────────────────────────────────────
        for u in SEED_USERS:
            existing = db.query(User).filter(User.email == u["email"]).first()
            if existing:
                print(f"  • {u['email']} already exists — skipping")
                continue
            user = User(
                name=u["name"],
                email=u["email"],
                password_hash=hash_password(u["password"]),
                role=u["role"],
                workspace_id=ws_map[u["ws"]],
            )
            db.add(user)
            print(f"  + Created {u['name']} ({u['role']})")

        db.commit()
        print("\nSeed complete.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()

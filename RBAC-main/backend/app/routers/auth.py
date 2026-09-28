"""Authentication & demo user-switching endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, SwitchUserRequest
from app.services.auth_service import (
    verify_password,
    create_token,
    get_current_user,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """Standard email/password login — returns a JWT."""
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(user)
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        name=user.name,
        role=user.role,
        workspace_id=user.workspace_id,
    )


@router.get("/me", response_model=dict)
def get_me(user: User = Depends(get_current_user)):
    """Return current user info — handy for the frontend to verify the token."""
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "workspace_id": user.workspace_id,
    }


# ── Demo-only endpoint ──────────────────────────────────────────────
# Intentionally simple: just pick a user_id and get a token.
# No real app would allow this — it exists purely so I can demo all
# four roles quickly without logging in/out each time.
@router.post("/switch-user", response_model=TokenResponse)
def switch_user(body: SwitchUserRequest, db: Session = Depends(get_db)):
    """DEMO-ONLY: Re-issue a JWT for any seed user by user_id.
    Clearly labelled in the frontend as a demo convenience panel."""
    user = db.query(User).filter(User.id == body.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    token = create_token(user)
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        name=user.name,
        role=user.role,
        workspace_id=user.workspace_id,
    )

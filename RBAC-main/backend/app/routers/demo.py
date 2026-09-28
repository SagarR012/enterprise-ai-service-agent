"""Demo convenience router — list all seed users for the Switch User panel."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserOut

router = APIRouter(prefix="/api/demo", tags=["demo"])


@router.get("/users", response_model=list[UserOut])
def list_seed_users(db: Session = Depends(get_db)):
    """List all users in the system (demo only — a real API would need admin auth)."""
    return db.query(User).order_by(User.role).all()

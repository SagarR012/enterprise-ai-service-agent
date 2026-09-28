"""Feedback recording — thumbs up/down on assistant responses."""
from sqlalchemy.orm import Session

from app.models.feedback import Feedback


def record_feedback(
    db: Session,
    message_id: str,
    user_id: str,
    rating: int,
    comment: str | None = None,
) -> Feedback:
    fb = Feedback(
        message_id=message_id,
        user_id=user_id,
        rating=rating,
        comment=comment,
    )
    db.add(fb)
    db.commit()
    db.refresh(fb)
    return fb

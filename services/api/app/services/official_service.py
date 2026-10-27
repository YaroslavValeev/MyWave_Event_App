"""Replace event officials from a parsed protocol."""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.official import Official
from app.models.user import User
from app.services.event_service import EventServiceError, can_write_events, get_event
from app.services.officials_parse import ParsedOfficial


def replace_officials(
    db: Session,
    *,
    event_id: int,
    actor: User,
    officials: list[ParsedOfficial],
    commit: bool = True,
) -> int:
    if not can_write_events(actor):
        raise EventServiceError("forbidden", "Недостаточно прав для судейского корпуса", 403)
    get_event(db, event_id=event_id, actor=actor, require_mutable=True)
    db.execute(delete(Official).where(Official.event_id == event_id))
    count = 0
    for item in officials:
        user_id = None
        if "валеев" in item.full_name.casefold():
            owner = db.scalar(select(User).where(User.email == "y.valeev@gmail.com"))
            if owner:
                user_id = owner.id
        db.add(
            Official(
                event_id=event_id,
                sort_order=item.sort_order,
                full_name=item.full_name[:255],
                position=item.position[:255],
                region=(item.region or None),
                judge_category=(item.judge_category or None),
                notes=item.notes,
                user_id=user_id,
            )
        )
        count += 1
    db.flush()
    if commit:
        db.commit()
    return count

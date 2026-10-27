"""Account ↔ Athlete claim after OTP. Never auto-merge by name."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.athlete import AccountAthleteLink, AthleteProfile
from app.models.user import User
from app.services.audit_service import append_audit
from app.services.phone_utils import mask_phone


class ClaimError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def list_links_for_user(db: Session, *, user: User) -> list[dict]:
    rows = list(
        db.scalars(
            select(AccountAthleteLink)
            .where(AccountAthleteLink.user_id == user.id)
            .order_by(AccountAthleteLink.id)
        ).all()
    )
    items: list[dict] = []
    for link in rows:
        profile = db.get(AthleteProfile, link.athlete_profile_id)
        if profile is None:
            continue
        items.append(
            {
                "id": link.id,
                "athlete_id": profile.athlete_id,
                "display_name": profile.display_name,
                "latin_name": profile.latin_name,
                "birth_year": profile.birth_year,
                "region": profile.region,
                "relation": link.relation,
                "status": link.status,
            }
        )
    return items


def _activate_if_ready(db: Session, user: User) -> None:
    if user.status != "pending_claim":
        return
    confirmed = db.scalar(
        select(AccountAthleteLink.id)
        .where(
            AccountAthleteLink.user_id == user.id,
            AccountAthleteLink.status == "confirmed",
        )
        .limit(1)
    )
    if confirmed:
        user.status = "active"
        db.add(user)


def confirm_link(
    db: Session,
    *,
    user: User,
    link_id: int,
    audit_enabled: bool = True,
) -> AccountAthleteLink:
    link = db.get(AccountAthleteLink, link_id)
    if link is None or link.user_id != user.id:
        raise ClaimError("not_found", "Связь не найдена", 404)
    if link.status == "confirmed":
        return link
    if link.status not in {"pending_claim", "disputed"}:
        raise ClaimError("invalid_status", "Эту связь нельзя подтвердить", 409)

    taken = db.scalar(
        select(AccountAthleteLink).where(
            AccountAthleteLink.athlete_profile_id == link.athlete_profile_id,
            AccountAthleteLink.status == "confirmed",
            AccountAthleteLink.relation == "self",
            AccountAthleteLink.user_id != user.id,
        )
    )
    if taken is not None and link.relation == "self":
        raise ClaimError(
            "profile_taken",
            "Этот профиль уже подтверждён другим аккаунтом. Обратитесь к организатору.",
            409,
        )

    link.status = "confirmed"
    link.confirmed_at = datetime.now(timezone.utc)
    db.add(link)
    db.flush()
    if link.relation == "self":
        profile = db.get(AthleteProfile, link.athlete_profile_id)
        if profile and not user.athlete_id:
            holder = db.scalar(select(User.id).where(User.athlete_id == profile.athlete_id))
            if holder is None:
                user.athlete_id = profile.athlete_id
                db.add(user)
    _activate_if_ready(db, user)
    append_audit(
        db,
        action="auth.athlete_link.confirm",
        actor_user_id=user.id,
        actor_email=user.email,
        entity_type="athlete_profile",
        entity_id=str(link.athlete_profile_id),
        payload={"link_id": link.id, "relation": link.relation, "phone_masked": mask_phone(user.phone)},
        enabled=audit_enabled,
    )
    db.commit()
    db.refresh(link)
    return link


def reject_link(
    db: Session,
    *,
    user: User,
    link_id: int,
    audit_enabled: bool = True,
) -> AccountAthleteLink:
    link = db.get(AccountAthleteLink, link_id)
    if link is None or link.user_id != user.id:
        raise ClaimError("not_found", "Связь не найдена", 404)
    if link.status == "confirmed":
        raise ClaimError("already_confirmed", "Подтверждённую связь нельзя отклонить здесь", 409)
    link.status = "rejected"
    db.add(link)
    db.flush()
    append_audit(
        db,
        action="auth.athlete_link.reject",
        actor_user_id=user.id,
        actor_email=user.email,
        entity_type="athlete_profile",
        entity_id=str(link.athlete_profile_id),
        payload={"link_id": link.id},
        enabled=audit_enabled,
    )
    db.commit()
    db.refresh(link)
    return link

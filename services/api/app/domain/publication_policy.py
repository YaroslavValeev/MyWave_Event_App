"""RBAC capabilities for event publications (ADR-0013)."""

from __future__ import annotations

from app.domain.roles import EVENT_WRITE_ROLES, Role
from app.models.user import User

POST_CREATE_ROLES: frozenset[Role] = frozenset(
    {
        Role.media,
        Role.commentator,
        Role.organizer,
        Role.federation_manager,
        Role.event_admin,
        Role.platform_admin,
    }
)

NEWS_CREATE_ROLES: frozenset[Role] = frozenset(EVENT_WRITE_ROLES)

PUBLISH_DIRECT_ROLES: frozenset[Role] = frozenset(EVENT_WRITE_ROLES)

MODERATE_ROLES: frozenset[Role] = frozenset(EVENT_WRITE_ROLES)

PUBLICATION_TYPES = frozenset({"post", "news"})
SERVER_STATUSES = frozenset(
    {"draft", "pending_moderation", "published", "rejected", "void"}
)

ALLOWED_MEDIA_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png", ".webp"})
ALLOWED_MEDIA_MIME = frozenset({"image/jpeg", "image/png", "image/webp"})
MAX_MEDIA_BYTES = 10 * 1024 * 1024


def role_of(user: User) -> Role:
    return Role(user.role)


def can_create_post(user: User) -> bool:
    return role_of(user) in POST_CREATE_ROLES


def can_create_news(user: User) -> bool:
    return role_of(user) in NEWS_CREATE_ROLES


def can_create_type(user: User, pub_type: str) -> bool:
    if pub_type == "post":
        return can_create_post(user)
    if pub_type == "news":
        return can_create_news(user)
    return False


def can_publish_direct(user: User) -> bool:
    return role_of(user) in PUBLISH_DIRECT_ROLES


def can_moderate(user: User) -> bool:
    return role_of(user) in MODERATE_ROLES


def assert_author_role(user: User, author_role: str) -> Role:
    """Reject publishing under a role the actor does not currently hold."""
    current = role_of(user)
    try:
        requested = Role(author_role)
    except ValueError as exc:
        raise ValueError("invalid_author_role") from exc
    if requested != current:
        raise PermissionError("author_role_mismatch")
    return current

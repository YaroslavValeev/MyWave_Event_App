"""Role taxonomy for MyWave Event App."""

from __future__ import annotations

from enum import Enum


class Role(str, Enum):
    participant = "participant"
    organizer = "organizer"
    judge = "judge"
    commentator = "commentator"
    media = "media"
    support = "support"
    federation_manager = "federation_manager"
    event_admin = "event_admin"
    platform_admin = "platform_admin"


# Roles that may create/update events (organizer+).
EVENT_WRITE_ROLES: frozenset[Role] = frozenset(
    {
        Role.organizer,
        Role.federation_manager,
        Role.event_admin,
        Role.platform_admin,
    }
)

# Roles that may read all events (including non-published).
EVENT_ADMIN_READ_ROLES: frozenset[Role] = frozenset(
    {
        Role.organizer,
        Role.federation_manager,
        Role.event_admin,
        Role.platform_admin,
    }
)

AUDIT_READ_ROLES: frozenset[Role] = frozenset(
    {
        Role.event_admin,
        Role.platform_admin,
    }
)


def parse_role(value: str | Role) -> Role:
    if isinstance(value, Role):
        return value
    return Role(value)

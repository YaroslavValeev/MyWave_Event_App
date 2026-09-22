"""Role taxonomy for MyWave Event App."""

from __future__ import annotations

from enum import Enum


class Role(str, Enum):
    participant = "participant"
    organizer = "organizer"
    judge = "judge"
    chief_judge = "chief_judge"
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
        Role.chief_judge,
    }
)

AUDIT_READ_ROLES: frozenset[Role] = frozenset(
    {
        Role.event_admin,
        Role.platform_admin,
    }
)

# Organizer/scorer verifies drafts; chief judge (or platform_admin) publishes.
RESULT_VERIFY_ROLES: frozenset[Role] = EVENT_WRITE_ROLES | frozenset({Role.chief_judge})
RESULT_PUBLISH_ROLES: frozenset[Role] = frozenset({Role.chief_judge, Role.platform_admin})
ROSTER_LOCK_ROLES: frozenset[Role] = EVENT_WRITE_ROLES
JUDGE_SCORE_ROLES: frozenset[Role] = EVENT_WRITE_ROLES | frozenset({Role.judge, Role.chief_judge})
# Organizer+ and chief judge may remove a rider from a heat start list.
START_LIST_REMOVE_ROLES: frozenset[Role] = EVENT_WRITE_ROLES | frozenset({Role.chief_judge})


def parse_role(value: str | Role) -> Role:
    if isinstance(value, Role):
        return value
    return Role(value)

"""Apply transcribed Kazan scan sheets into the Kazan event. Photos stay out of git."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_DIR = ROOT / "services" / "api"
sys.path.insert(0, str(API_DIR))

from sqlalchemy import select  # noqa: E402

from app.db import get_session_factory, init_db  # noqa: E402
from app.models.event import Event  # noqa: E402
from app.models.user import User  # noqa: E402
from app.services.protocol_pack_service import apply_scan_protocol  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--event-id", type=int, default=None)
    args = parser.parse_args()

    init_db()
    db = get_session_factory()()
    try:
        event = None
        if args.event_id:
            event = db.get(Event, args.event_id)
        if event is None:
            event = db.scalar(select(Event).where(Event.slug == "chr-pr-kazan-2026"))
        if event is None:
            event = db.scalar(select(Event).where(Event.title.like("%Казан%")))
        if event is None:
            raise SystemExit("Событие Казань не найдено. Укажите --event-id.")
        actor = db.scalar(select(User).where(User.role.in_(("platform_admin", "organizer"))))
        if actor is None:
            raise SystemExit("Нет пользователя organizer/platform_admin.")
        result = apply_scan_protocol(db, event_id=event.id, actor=actor)
        print(
            f"Scan protocol → event {event.id} «{event.title}»: "
            f"heats={result['heats']} entries={result['entries']} "
            f"results={result['results']} dns={result['dns']}"
        )
        print("Results remain draft (Not homologated). Do not auto-publish.")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())

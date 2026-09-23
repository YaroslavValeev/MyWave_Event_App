"""Load owner-provided Kazan documents into one event. Files stay outside git."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_DIR = ROOT / "services" / "api"
sys.path.insert(0, str(API_DIR))

from sqlalchemy import select  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.db import get_session_factory, init_db  # noqa: E402
from app.models.event import Event  # noqa: E402
from app.models.user import User  # noqa: E402
from app.services.event_pack_service import ingest_pack  # noqa: E402

DEFAULT_DIR = Path(r"c:\Users\X230\Downloads\Telegram Desktop")
DEFAULT_FILES = [
    "Регистрация_ЧР_ПР_2026_по_категориям.xlsx",
    "u14_jun_wakeboard_qualifications_startlist.pdf",
    "u14_u18_wake_skim_qualifications_startlist.pdf",
    "32_протокол_КС_ЧР_Казань_доска_короткая,_длинная_260714_172154.pdf",
]


def _find(base: Path, name: str) -> Path | None:
    direct = base / name
    if direct.exists():
        return direct
    key = name.casefold()[:20]
    for path in base.iterdir():
        if path.name.casefold() == name.casefold() or key in path.name.casefold():
            return path
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", type=Path, default=DEFAULT_DIR)
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
        files: list[tuple[str, bytes]] = []
        for name in DEFAULT_FILES:
            path = _find(args.dir, name)
            if path is None:
                print(f"SKIP missing {name}")
                continue
            files.append((path.name, path.read_bytes()))
            print(f"OK {path.name} ({path.stat().st_size} bytes)")
        if not files:
            raise SystemExit("Нет файлов для загрузки.")
        result = ingest_pack(
            db,
            event_id=event.id,
            actor=actor,
            files=files,
            repo_root=get_settings().repo_root,
        )
        print(
            f"Loaded into event {event.id} «{event.title}»: "
            f"officials={result['officials']} start_entries={result['start_entries']}"
        )
        for item in result["files"]:
            print(" ", item)
        from app.services.protocol_pack_service import apply_scan_protocol  # noqa: E402

        scans = apply_scan_protocol(db, event_id=event.id, actor=actor)
        print(
            f"Scans: heats={scans['heats']} entries={scans['entries']} "
            f"results={scans['results']} dns={scans['dns']} (draft, not homologated)"
        )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())

"""Scoreboard + SSE stream — ADR-0016."""

from __future__ import annotations

import asyncio
import json
from typing import Annotated

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import DbSession, OptionalUser, get_db
from app.api.errors import raise_api_error
from app.services.event_service import EventServiceError
from app.services.scoreboard_service import build_scoreboard

router = APIRouter(prefix="/events", tags=["scoreboard"])


@router.get("/{event_id}/scoreboard")
def get_scoreboard(
    event_id: int,
    db: DbSession,
    user: OptionalUser,
    include_unofficial: Annotated[bool, Query()] = False,
) -> dict:
    try:
        return build_scoreboard(
            db,
            event_id=event_id,
            actor=user,
            include_unofficial=include_unofficial,
        )
    except EventServiceError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)


@router.get("/{event_id}/scoreboard/stream")
async def scoreboard_stream(
    event_id: int,
    user: OptionalUser,
    include_unofficial: Annotated[bool, Query()] = False,
):
    """SSE: emits `scoreboard` events when revision changes."""

    async def event_gen():
        last_rev: str | None = None
        # Independent short-lived sessions per tick (avoid holding one request session forever).
        while True:
            db: Session = next(get_db())
            try:
                board = build_scoreboard(
                    db,
                    event_id=event_id,
                    actor=user,
                    include_unofficial=include_unofficial,
                )
            except EventServiceError as exc:
                payload = json.dumps({"error": {"code": exc.code, "message": exc.message}})
                yield f"event: error\ndata: {payload}\n\n"
                break
            finally:
                db.close()

            rev = board["revision"]
            if rev != last_rev:
                last_rev = rev
                yield f"event: scoreboard\ndata: {json.dumps(board, ensure_ascii=False)}\n\n"
            else:
                yield f"event: ping\ndata: {json.dumps({'revision': rev})}\n\n"
            await asyncio.sleep(2.0)

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

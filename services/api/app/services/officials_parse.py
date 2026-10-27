"""Parse FVLS judging-college protocol (протокол КС) text."""

from __future__ import annotations

import re
from dataclasses import dataclass

POSITIONS = (
    "Главный судья",
    "Главный секретарь",
    "Судья арбитр в катере",
    "Судья водитель катера",
    "Судья при участниках",
    "Судья комментатор",
)


@dataclass
class ParsedOfficial:
    sort_order: int
    full_name: str
    position: str
    region: str | None
    judge_category: str | None
    notes: str | None = None


_POS_ALT = "|".join(re.escape(p) for p in POSITIONS)
ROW_RE = re.compile(
    rf"^(?P<n>\d+)\s+(?P<pos>{_POS_ALT})\s+(?P<rest>.+)$",
    re.M,
)


def parse_ks_protocol_text(text: str) -> list[ParsedOfficial]:
    if not text.strip():
        return []
    officials: list[ParsedOfficial] = []
    for match in ROW_RE.finditer(text):
        rest = re.sub(r"\s+", " ", match.group("rest")).strip()
        pos = match.group("pos")
        sort_order = int(match.group("n"))
        judge_cat = None
        cat_m = re.search(r"\b(\d?К|ВК(?:,\s*МК)?|МК)\s*$", rest, re.I)
        if cat_m:
            judge_cat = cat_m.group(1).replace(" ", "")
            rest = rest[: cat_m.start()].strip()
        region = None
        region_m = re.search(
            r"(г\.\s*.+|Г\.\s*.+|Самарская область|Республика Татарстан|Москва|Санкт-Петербург)\s*$",
            rest,
            re.I,
        )
        if region_m:
            region = region_m.group(1).strip()
            rest = rest[: region_m.start()].strip()
        name = rest.strip(" -")
        notes = None
        if pos == "Судья при участниках" and (not name or "татарстан" in name.casefold() or "фвсрт" in name.casefold()):
            name = "По назначению ФВСРТ"
            notes = "ФИО в протоколе не указано"
            if region is None:
                region = "Республика Татарстан"
        if not name:
            continue
        officials.append(
            ParsedOfficial(
                sort_order=sort_order,
                full_name=name,
                position=pos,
                region=region,
                judge_category=judge_cat,
                notes=notes or "Протокол №32-КС от 13.07.2026",
            )
        )
    return officials

"""Parse IWWF-style qualification start list PDFs (text layer)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

HEAT_HEAD_RE = re.compile(
    r"(?P<title>.+?)\s+Qualifications Starting list\s+(?P<dow>\w+)\s*-\s*(?P<time>\d{1,2}:\d{2})",
    re.I,
)
STARTER_RE = re.compile(
    r"^(?P<order>\d+)\s+(?P<name>[A-Za-z][A-Za-z_.'-]*(?:\s+[A-Za-z][A-Za-z_.'-]*)+)"
    r"(?:\s+RUS)?\s+(?P<cat>U\d+|Jun|JUN|Open|Grom)?\s*(?P<sex>[MF])?\s*$",
    re.M,
)

DOW_TO_DATE_2026 = {
    "thursday": (2026, 8, 13),
    "friday": (2026, 8, 14),
    "saturday": (2026, 8, 15),
    "sunday": (2026, 8, 16),
}


@dataclass
class ParsedStarter:
    start_order: int
    latin_name: str
    category_code: str | None
    sex: str | None


@dataclass
class ParsedStartHeat:
    title: str
    discipline: str
    age_key: str
    sex: str
    round_key: str
    weekday: str
    time_hm: str
    year: int
    month: int
    day: int
    homologation: str | None
    starters: list[ParsedStarter] = field(default_factory=list)


def _norm_name(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("_", " ").strip())


def _discipline(title: str) -> str:
    low = title.casefold()
    if "skim" in low:
        return "Wakeskim"
    if "surf" in low:
        return "Wakesurf"
    return "Wakeboard (boat)"


def _age_and_sex(title: str, first: ParsedStarter | None) -> tuple[str, str]:
    low = title.casefold()
    sex = "f" if any(w in low for w in ("girl", "women", "woman", "ladies")) else "m"
    if first and first.sex:
        sex = first.sex.lower()
    if "grom" in low:
        return "u14", sex
    if "under 14" in low or "u14" in low:
        return "u14", sex
    if "under 18" in low or "u18" in low:
        return "u18", sex
    if "junior" in low or re.search(r"\bjun\b", low):
        return "u18", sex
    if "open" in low or "master" in low:
        return "open", sex
    if first and first.category_code:
        code = first.category_code.casefold()
        if code.startswith("u"):
            return code, sex
        if code == "jun":
            return "u18", sex
    return "open", sex


def parse_startlist_text(text: str) -> list[ParsedStartHeat]:
    if not text.strip():
        return []
    homologation = None
    homo = re.search(r"Homologation:\s*(.+)", text, re.I)
    if homo:
        homologation = homo.group(1).strip()

    heads = list(HEAT_HEAD_RE.finditer(text))
    heats: list[ParsedStartHeat] = []
    for idx, match in enumerate(heads):
        start = match.end()
        end = heads[idx + 1].start() if idx + 1 < len(heads) else len(text)
        chunk = text[start:end]
        starters: list[ParsedStarter] = []
        for row in STARTER_RE.finditer(chunk):
            cat = row.group("cat")
            starters.append(
                ParsedStarter(
                    start_order=int(row.group("order")),
                    latin_name=_norm_name(row.group("name")),
                    category_code=cat.upper() if cat else None,
                    sex=(row.group("sex") or "").lower() or None,
                )
            )
        title = re.sub(r"\s+", " ", match.group("title")).strip()
        first = starters[0] if starters else None
        age_key, sex = _age_and_sex(title, first)
        dow = match.group("dow").casefold()
        y, m, d = DOW_TO_DATE_2026.get(dow, (2026, 8, 13))
        heats.append(
            ParsedStartHeat(
                title=title,
                discipline=_discipline(title),
                age_key=age_key,
                sex=sex,
                round_key="qual",
                weekday=dow,
                time_hm=match.group("time"),
                year=y,
                month=m,
                day=d,
                homologation=homologation,
                starters=starters,
            )
        )
    return heats

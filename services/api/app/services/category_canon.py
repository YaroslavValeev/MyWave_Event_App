"""IWWF category canon for Kazan 2026 (ADR-0007 accepted).

One event = ЧР + ПР together.
Canonical classes: U14, U18, O30, O40, Open (Open = чемпионат).
Age is computed as of 31 December of the competition year.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

COMPETITION_YEAR = 2026
IWWF_CLASSES = ("U14", "U18", "O30", "O40", "Open")

FEMALE_TOKENS = (
    "девоч",
    "девуш",
    "женщин",
    "жен.",
    "girl",
    "women",
    "woman",
    "ladies",
    " female",
    " f ",
)
MALE_TOKENS = (
    "мальчи",
    "юнош",
    "мужчин",
    "муж.",
    "boy",
    "men",
    "man",
    "grom",
    " male",
    " m ",
)

DISCIPLINE_SLUG = {
    "Wakeboard (boat)": "wb",
    "Wakesurf": "ws",
    "Wakeskim": "wk",
}


@dataclass(frozen=True)
class CanonicalCategory:
    iwwf_class: str
    sex: str  # f | m | x
    code: str
    title: str
    source_label: str | None = None


def age_on_dec31(birth_year: int | None, *, year: int = COMPETITION_YEAR) -> int | None:
    if birth_year is None:
        return None
    if birth_year < 1900 or birth_year > year:
        return None
    return year - birth_year


def sex_from_label(label: str | None) -> str:
    if not label:
        return "x"
    padded = f" {label.casefold()} "
    if any(tok in padded for tok in FEMALE_TOKENS) or padded.strip().endswith(" f") or " f)" in padded:
        return "f"
    if any(tok in padded for tok in MALE_TOKENS) or padded.strip().endswith(" m") or " m)" in padded:
        return "m"
    low = label.casefold()
    if re.search(r"\bf\b", low) and not re.search(r"\bm\b", low):
        return "f"
    if re.search(r"\bm\b", low) and not re.search(r"\bf\b", low):
        return "m"
    return "x"


def _youth_or_masters_class(label: str) -> str | None:
    low = label.casefold()
    if "grom" in low or "u14" in low or "under 14" in low or "до 15" in low:
        return "U14"
    if "junior" in low or re.search(r"\bjun\b", low) or "u18" in low or "under 18" in low or "до 19" in low:
        return "U18"
    if "девоч" in low or "мальчи" in low:
        return "U14"
    if "девуш" in low or "юнош" in low:
        return "U18"
    if "o40" in low or "40+" in low or "40 +" in low or "ветеран" in low:
        return "O40"
    if "o30" in low or "30+" in low or "30 +" in low or "мастер" in low:
        return "O30"
    return None


def iwwf_class_from_source(label: str | None, *, birth_year: int | None) -> str:
    """Map a source label to U14 / U18 / O30 / O40 / Open.

    Youth labels win over computed age. Adult Open/Женщины/Мужчины split by age.
    """
    text = (label or "").strip()
    if text:
        locked = _youth_or_masters_class(text)
        if locked:
            return locked
    age = age_on_dec31(birth_year)
    if age is not None and age >= 40:
        return "O40"
    if age is not None and age >= 30:
        return "O30"
    return "Open"


def category_code(discipline: str | None, iwwf_class: str, sex: str) -> str:
    disc = DISCIPLINE_SLUG.get(discipline or "", None)
    if not disc:
        slug = re.sub(r"[^a-z0-9]+", "-", (discipline or "disc").casefold()).strip("-")[:16]
        disc = slug or "disc"
    sex_bit = sex if sex in {"f", "m"} else "x"
    return f"{disc}-{iwwf_class.lower()}-{sex_bit}"


def category_title(iwwf_class: str, sex: str) -> str:
    sex_ru = {"f": "жен.", "m": "муж."}.get(sex, "")
    if iwwf_class == "Open":
        core = "Open (чемпионат)"
    elif iwwf_class in {"U14", "U18"}:
        core = f"{iwwf_class} (первенство)"
    elif iwwf_class == "O30":
        core = "O30 (мастерс)"
    elif iwwf_class == "O40":
        core = "O40 (ветераны)"
    else:
        core = iwwf_class
    if sex_ru:
        return f"{core} · {sex_ru}"
    return core


def canonical_category(
    label: str | None,
    *,
    discipline: str | None,
    birth_year: int | None = None,
    sex_hint: str | None = None,
) -> CanonicalCategory:
    iwwf = iwwf_class_from_source(label, birth_year=birth_year)
    sex = (sex_hint or "").lower() if sex_hint in {"f", "m", "x"} else sex_from_label(label)
    if sex == "x" and sex_hint in {"f", "m"}:
        sex = sex_hint
    return CanonicalCategory(
        iwwf_class=iwwf,
        sex=sex,
        code=category_code(discipline, iwwf, sex),
        title=category_title(iwwf, sex),
        source_label=label,
    )

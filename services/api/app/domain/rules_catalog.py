"""Governing bodies, disciplines, rules packs — Stage 1 catalog."""

from __future__ import annotations

GOVERNING_BODIES: dict[str, dict[str, str]] = {
    "FVLS": {"title": "Федерация вейкспорта и водных лыж", "default_sanction": "IWWF"},
    "IWWF": {"title": "International Waterski & Wakeboard Federation"},
    "WSWS": {"title": "World Series of Wake Surfing", "affiliation": "WWA"},
    "WWA": {"title": "World Wake Association"},
    "CWSA": {"title": "Canadian Wakeboard & Ski Association", "status": "reserved"},
}

DISCIPLINES: dict[str, dict[str, str]] = {
    "wakeboard_boat": {"title_ru": "Вейкборд (катер)", "default_rules_pack": "IWWF_BOAT_EIC_2025"},
    "wakeboard_cable": {
        "title_ru": "Cable wakeboard / электротяга",
        "default_rules_pack": "IWWF_CABLE_TI_2025",
    },
    "wakesurf_boat": {
        "title_ru": "Вейксерф",
        "default_rules_pack": "WSWS_WAKESURF_DRIVE",
    },
    "wakeskim": {"title_ru": "Вейкским", "default_rules_pack": "MANUAL_PLACE_v1"},
}

RULES_PACKS: dict[str, dict[str, object]] = {
    "IWWF_BOAT_EIC_2025": {"engine": "IWWF_BOAT_EIC", "max_score": 100},
    "IWWF_CABLE_TI_2025": {"engine": "IWWF_CABLE_TI", "max_score": 100, "scorenow_alternative": True},
    "IWWF_WAKESURF_2024": {"engine": "IWWF_WAKESURF_SUBJECTIVE", "max_score": 100},
    "WSWS_WAKESURF_DRIVE": {
        "engine": "WSWS_DRIVE",
        "max_score": 100,
        "criteria": ["difficulty", "risk", "intensity", "variety", "execution"],
        "supports_judge_sheet_photo": True,
    },
    "MANUAL_PLACE_v1": {"engine": "MANUAL_PLACE", "supports_photo_protocol": True},
}

SCORING_MODES: dict[str, dict[str, str]] = {
    "structured": {"title_ru": "Судьи в приложении"},
    "manual": {"title_ru": "Ручной ввод протокола"},
    "photo_protocol": {"title_ru": "Фото / PDF протокола"},
    "import_scorenow": {"title_ru": "Импорт Score-now"},
    "import_excel": {"title_ru": "Импорт Excel (WSWS и др.)"},
}

P0_DISCIPLINE_CODES = frozenset(
    {"wakeboard_boat", "wakeboard_cable", "wakesurf_boat", "wakeskim"}
)

DEFAULT_GOVERNING_BODY = "FVLS"
DEFAULT_SANCTION_BODY = "IWWF"
DEFAULT_SCORING_MODE = "photo_protocol"


def default_rules_pack_for(discipline_code: str) -> str:
    meta = DISCIPLINES.get(discipline_code)
    if meta is None:
        raise ValueError(f"unknown discipline: {discipline_code}")
    return str(meta["default_rules_pack"])


def catalog_payload() -> dict[str, object]:
    return {
        "governing_bodies": GOVERNING_BODIES,
        "disciplines": DISCIPLINES,
        "rules_packs": RULES_PACKS,
        "scoring_modes": SCORING_MODES,
        "p0_discipline_codes": sorted(P0_DISCIPLINE_CODES),
        "defaults": {
            "governing_body": DEFAULT_GOVERNING_BODY,
            "sanction_body": DEFAULT_SANCTION_BODY,
            "scoring_mode": DEFAULT_SCORING_MODE,
        },
    }

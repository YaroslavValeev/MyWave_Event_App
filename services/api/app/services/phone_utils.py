"""Phone number normalization helpers (RU-centric)."""

from __future__ import annotations

import re


def normalize_phone(raw: str | None) -> str | None:
    if raw is None:
        return None
    text = str(raw).strip()
    if not text or text.lower() in {"none", "null", "-"}:
        return None
    # Excel sometimes stores phones as floats
    if re.fullmatch(r"\d+\.0+", text):
        text = text.split(".", 1)[0]
    digits = re.sub(r"\D+", "", text)
    if not digits:
        return None
    if len(digits) == 11 and digits.startswith("8"):
        digits = "7" + digits[1:]
    if len(digits) == 10:
        digits = "7" + digits
    if len(digits) == 11 and digits.startswith("7"):
        return f"+{digits}"
    if len(digits) >= 11:
        return f"+{digits}"
    return None


def mask_phone(phone: str | None) -> str | None:
    if not phone:
        return None
    digits = re.sub(r"\D+", "", phone)
    if len(digits) < 4:
        return "***"
    return f"+{digits[0]}***{digits[-4:]}"


def mask_email(email: str | None) -> str | None:
    if not email or "@" not in email:
        return None
    local, domain = email.split("@", 1)
    if len(local) <= 1:
        masked_local = "•••"
    elif len(local) == 2:
        masked_local = f"{local[0]}•"
    else:
        masked_local = f"{local[0]}•••{local[-1]}"
    return f"{masked_local}@{domain}"

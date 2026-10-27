"""Extract text from PDF bytes. No logging of page content."""

from __future__ import annotations

from io import BytesIO


def extract_pdf_text(payload: bytes) -> str:
    if not payload:
        return ""
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("pypdf is required to parse PDF documents") from exc
    reader = PdfReader(BytesIO(payload))
    parts: list[str] = []
    for page in reader.pages:
        parts.append(page.extract_text() or "")
    return "\n".join(parts)

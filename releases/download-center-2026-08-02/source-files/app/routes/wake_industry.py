"""
Blueprint для страницы "Индустрия вейка" с чеклистом условий для соревнований.
"""

from io import BytesIO

from flask import Blueprint, Response, jsonify, render_template, request

from app.extensions import csrf, limiter
from app.services.event_app_downloads import (
    DownloadConfigurationError,
    build_handoff,
    build_public_manifest,
    build_unavailable_manifest,
    get_artifact_status,
)
from app.services.rate_limit import limit_by_config

wake_industry_bp = Blueprint("wake_industry", __name__)


@wake_industry_bp.app_context_processor
def inject_event_app_downloads():
    """Provide release metadata only to the canonical checklist page."""
    if request.path.rstrip("/") != "/projects/checklist-org":
        return {}
    try:
        manifest = build_public_manifest()
    except DownloadConfigurationError:
        manifest = build_unavailable_manifest()
    return {"event_app_downloads": manifest}


def _handoff_rate_limit(view_func):
    return limit_by_config(limiter, "20 per minute", methods=["POST"])(view_func)


@wake_industry_bp.after_request
def protect_download_api(response):
    if request.path.startswith("/api/event-app-downloads/"):
        response.headers["Cache-Control"] = "no-store, max-age=0"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
    return response


@wake_industry_bp.get("/api/event-app-downloads/manifest")
def event_app_manifest():
    try:
        return jsonify(build_public_manifest())
    except DownloadConfigurationError:
        return (
            jsonify(
                error="manifest_unavailable", message="Каталог временно недоступен."
            ),
            503,
        )


@wake_industry_bp.get("/api/event-app-downloads/<artifact_id>/status")
def event_app_artifact_status(artifact_id):
    try:
        artifact = get_artifact_status(artifact_id)
    except KeyError:
        return jsonify(error="artifact_not_found", message="Формат не найден."), 404
    except DownloadConfigurationError:
        return (
            jsonify(
                error="manifest_unavailable", message="Каталог временно недоступен."
            ),
            503,
        )
    status_code = 503 if artifact["state"] == "error" else 200
    return jsonify(artifact), status_code


@wake_industry_bp.post("/api/event-app-downloads/<artifact_id>/handoff")
@csrf.exempt
@_handoff_rate_limit
def event_app_artifact_handoff(artifact_id):
    try:
        return jsonify(build_handoff(artifact_id))
    except KeyError:
        return jsonify(error="artifact_not_found", message="Формат не найден."), 404
    except DownloadConfigurationError as exc:
        return jsonify(error="artifact_unavailable", message=str(exc)), 503


# Опциональный импорт weasyprint
try:
    from weasyprint import HTML

    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False


@wake_industry_bp.get("/wake-industry")
def wake_industry_redirect():
    """Legacy: редирект на канонический URL чеклиста."""
    from flask import redirect

    return redirect("/projects/checklist-org", code=301)


@wake_industry_bp.get("/wake-industry/download")
def download_checklist_pdf():
    """Генерация и скачивание PDF версии чеклиста."""
    if not WEASYPRINT_AVAILABLE:
        return (
            jsonify(
                {
                    "error": (
                        "PDF генерация недоступна. Установите weasyprint: "
                        "pip install weasyprint"
                    )
                }
            ),
            500,
        )

    try:
        # Рендерим HTML для PDF
        html_content = render_template("wake_industry/checklist_pdf.html")

        # Генерируем PDF
        pdf_file = BytesIO()
        HTML(string=html_content).write_pdf(pdf_file)
        pdf_file.seek(0)

        # Возвращаем PDF как ответ
        return Response(
            pdf_file.getvalue(),
            mimetype="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=wake-industry-checklist.pdf"
            },
        )
    except Exception as e:
        from app.modules.logger import get_logger

        logger = get_logger(__name__)
        logger.error(f"Ошибка генерации PDF: {e}", exc_info=True)
        return jsonify({"error": f"Ошибка генерации PDF: {str(e)}"}), 500

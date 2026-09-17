# SECURITY (Stage 1)

**Дата:** 2026-09-16

- Secrets только в `.env` / secret manager.
- `dev-login` запрещён вне development.
- JWT HS256; в production `SECRET_KEY` обязан быть уникальным (≥32 символов), иначе API не стартует.
- Email approve: GET без побочных эффектов; мутация только POST confirm (ADR-0005).
- OTP: не больше 5 запросов на номер за 10 минут.
- Pending role list не возвращает capability-token.
- RBAC enforced on API, not only UI. `published` result — `chief_judge` / `platform_admin`.
- Audit: login, event create/update, document upload/delete, checklist, heats/start-list.
- Document upload: organizer+ only; allowlist `.pdf` / `.xlsx` / `.xls` / `.docx`; max 25 MB; path containment under `data/documents/{slug}/`; filename sanitized; `access_class`; audit `document.upload` / `document.delete`.
- FieldMoment upload: media/commentator/support/organizer+/chief_judge; participant 403; guest 401; JPG/PNG/WebP/HEIC ≤15 MB, MP4/WebM/MOV ≤40 MB; path containment `data/field-media/{slug}/`; status approve только organizer+/chief_judge; файлы не на витрине; audit `field_moment.upload` / `field_moment.update`.
- Import Center: organizer+; xlsx ≤5 МБ; SHA-256 идемпотентность; телефоны в API только mask; medical URL не сохраняется; заполненные таблицы участников **запрещено** коммитить в git.
- Athlete ID не содержит ФИО/телефон; OTP нельзя обойти для pending_claim; confirm чужого профиля → 404.
- Media/photographer full workflow (EXIF, Athlete match, consent-публикация) — после стабилизации results; FieldMoment — только внутренние кадры команды события.
- Releases archive may contain site-integration patch; do not treat as runtime security model of this app.
- App downloads: target URLs only in env; manifest/status never include them; handoff rate-limited; no server-side fetch of target (no SSRF). Placeholders `{{...}}` are unavailable, not live links.

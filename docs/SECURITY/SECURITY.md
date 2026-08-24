# SECURITY (Stage 1)

- Secrets только в `.env` / secret manager.
- `dev-login` запрещён вне development.
- JWT HS256; в production `SECRET_KEY` обязан быть уникальным (≥32 символов), иначе API не стартует.
- Email approve: GET без побочных эффектов; мутация только POST confirm (ADR-0005).
- OTP: не больше 5 запросов на номер за 10 минут.
- Pending role list не возвращает capability-token.
- RBAC enforced on API, not only UI.
- Audit: login, event create/update.
- Upload/media policies — Этап 1.x+.
- Releases archive may contain site-integration patch; do not treat as runtime security model of this app.

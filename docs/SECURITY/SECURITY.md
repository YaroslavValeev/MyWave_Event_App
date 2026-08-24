# SECURITY (Stage 1)

- Secrets только в `.env` / secret manager.
- `dev-login` запрещён вне development.
- JWT HS256; сменить `SECRET_KEY` в production.
- RBAC enforced on API, not only UI.
- Audit: login, event create/update.
- Upload/media policies — Этап 1.x+.
- Releases archive may contain site-integration patch; do not treat as runtime security model of this app.

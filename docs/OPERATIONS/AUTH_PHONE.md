# Auth: phone login + registration

## Flows

1. **Register** `POST /api/v1/auth/register`
   - Fields: phone, email, display_name, requested_role
   - `participant` → `status=active`, JWT immediately
   - Any other role → `status=pending`, email with approve/reject links to `OWNER_APPROVAL_EMAIL` (default `y.valeev@gmail.com`)

2. **Phone login**
   - `GET /api/v1/auth/login-options` — UI смотрит `otp_required` (пароля нет: `password_required` всегда false)
   - Пока SMTP не настроен **и** `APP_ENV` не `production`: `POST /api/v1/auth/phone/login` выдаёт JWT по известному телефону. Роль **не выбирается на форме** — берётся из аккаунта. Неизвестный номер → 404, pending/rejected → 403.
   - Когда SMTP задан (`SMTP_HOST` + `SMTP_FROM`) или `APP_ENV=production`: `phone/login` → 403 `otp_required`. Тогда:
     - `POST /api/v1/auth/phone/request-otp` — OTP hashed in DB; code emailed to account + written to `data/mail_outbox/`
     - `POST /api/v1/auth/phone/verify-otp` — returns JWT if `status=active`
   - SMS delivery is intentionally deferred; until SMTP, local/staging вход без кода. Production OTP не отключать.

3. **Approve role** (owner)
   - Links in mail: `/api/v1/auth/approvals/{token}/approve|reject` — GET только показывает форму.
   - Мутация: `POST /api/v1/auth/approvals/{token}/confirm` (`decision=approve|reject`).
   - UI: `POST /api/v1/auth/approvals/{approval_id}/approve|reject` (Bearer, без token в списке).

4. **Dev login** remains for local bootstrap only (`APP_ENV=development|test`)

## Env

- `OWNER_APPROVAL_EMAIL=y.valeev@gmail.com`
- Optional SMTP: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`, `SMTP_USE_TLS`
- Without SMTP, letters land in `data/mail_outbox/`

## UI

- `/login` — телефон; код только если API требует OTP (SMTP или production)
- `/register` — registration form (при email/phone taken — CTA «Войти»)
- `/profile` — PATCH имя/телефон (`PATCH /api/v1/me`)
- `/admin/approvals` — очередь ролей for organizers/admins
- `/notifications` — in-app журнал статусов (заявка/роль), пока SMTP не настроен

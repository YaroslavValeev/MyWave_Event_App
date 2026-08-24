# CURRENT_STATE

Дата: 2026-08-24

## Работает

- Standalone продукт `MyWave_Event_App` (не плагин сайта).
- **Phone auth:** регистрация, OTP (email + `data/mail_outbox`), JWT, **PATCH `/me`** (имя + телефон).
- **Роли:** `participant` auto-approve; остальные → pending + approve (email / UI `/admin/approvals`).
- **Consent Stage 1:** обязательные `terms_of_use` + `privacy_policy` при регистрации; опциональные публикация имени и аналитика; профиль умеет grant/revoke опциональных; публичный roster маскирует self-serve ФИО без publish-consent.
- Seed Казань 2026 из **Google Form Excel** (primary): **97** заявок/участников, **17** кат., **51** медфлаг, **11** судей, **162** слота (35 booked), **83** phone-users; owner `y.valeev@gmail.com` ↔ `+79160117179`.
- Web: `/`, `/login`, `/register` (чекбоксы документов + CTA «Войти» при email/phone taken), `/legal/[purpose]`, `/profile` (согласия), `/events`, `/events/new`, `/events/[id]` (табы: Обзор / Участники / Слоты / Документы / Заявки), `/admin/approvals`, `/health`.
- Self-serve заявка: `POST .../applications` → pending → organizer accept/reject.
- Публичный roster: `has_medical_cert` bool; **без** phone и **без** medical URL; self-serve без publish-consent → «Участник №id».
- CI: `.github/workflows/ci.yml` (pytest + next build). Pytest: **29 passed**.

## Частично

- OTP/approve без SMTP идут в outbox (нужен Gmail App Password для боевой почты).
- Seed-пользователи: email `p{phone}@participants.mywave.local` (не личные почты спортсменов).
- Тексты `docs/LEGAL/*` — рабочие редакции Stage 1, не юридическая экспертиза.
- SMS-доставка OTP — позже.

## Отсутствует / владелец

- Production SMTP (Gmail App Password).
- Staging deploy.
- Heats / день соревнований отдельно от training slots.
- Транспорт продуктовой аналитики (согласие уже пишется).

## Следующий P0 (owner)

1. SMTP владельца (см. `OWNER_COMMANDS.md`)
2. Staging deploy

## Следующий P0 (код, незаблокированный)

In-app журнал уведомлений (заявка/роль) без внешнего SMTP — чтобы критичные статусы были видны в UI, пока почта не настроена.

## Проверки

- `npm run reseed` — seed Form Excel + restart API
- `pytest` в `services/api` (venv `C:\tmp\mw_event_api_venv`) — 29 passed
- Smoke: `/health`, `/login`, `/register`, `/legal/terms_of_use`, `/events/1`, `/profile`

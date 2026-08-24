# CURRENT_STATE

Дата: 2026-08-24  
Версия продукта: **0.4.0**  
Путь до DoD v1 (аудит): ~**32%**

## Работает

- Standalone продукт `MyWave_Event_App` (не плагин сайта).
- **Phone auth:** регистрация, OTP (email + `data/mail_outbox`), JWT, **PATCH `/me`** (имя + телефон).
- **Роли:** `participant` auto-approve; остальные → pending + approve (email confirm POST / UI `/admin/approvals`).
- **Consent Stage 1:** обязательные `terms_of_use` + `privacy_policy` при регистрации; опциональные публикация имени и аналитика; профиль умеет grant/revoke опциональных; публичный roster маскирует self-serve ФИО без publish-consent.
- **In-app уведомления:** журнал `/notifications` + API `/me/notifications` для статусов заявки и роли (без SMTP).
- **Email approve:** GET только форма подтверждения; мутация через POST confirm. Pending list не отдаёт token.
- **OTP rate limit:** не больше 5 запросов кода на номер за 10 минут.
- **Production SECRET_KEY:** отказ стартовать с дефолтным/коротким ключом.
- Seed Казань 2026 из **Google Form Excel** (primary): **97** заявок/участников, **17** кат., **51** медфлаг, **11** судей, **162** слота (35 booked), **83** phone-users; owner `y.valeev@gmail.com` ↔ `+79160117179`.
- Web: `/`, `/login`, `/register`, `/legal/[purpose]`, `/profile`, `/notifications`, `/events`, `/events/new`, `/events/[id]`, `/admin/approvals`, `/health`.
- Self-serve заявка: `POST .../applications` → pending → organizer accept/reject.
- Публичный roster: `has_medical_cert` bool; **без** phone и **без** medical URL; self-serve без publish-consent → «Участник №id».
- CI: `.github/workflows/ci.yml` (pytest + next build); release gate: `.github/workflows/release.yml` на tags `v*`.
- Staging runbook: `docs/OPERATIONS/STAGING.md` + `docker-compose.staging.yml`.
- Roadmap переведён на Competition Platform DoD v1 (`docs/PRODUCT/ROADMAP.md`).

## Частично

- OTP/approve без SMTP идут в outbox (нужен Gmail App Password для боевой почты).
- Seed-пользователи: email `p{phone}@participants.mywave.local` (не личные почты спортсменов).
- Тексты `docs/LEGAL/*` — рабочие редакции Stage 1, не юридическая экспертиза.
- SMS-доставка OTP — позже.
- Staging compose готов; remote host ещё не подключён.
- Git remote: **https://github.com/YaroslavValeev/MyWave_Event_App** (private); tag `v0.4.0` запушен.

## Отсутствует

- Production SMTP.
- Remote staging deploy evidence (compose/runbook готовы).
- Heats / start lists / competition day (≠ training slots).
- Results / protocols / Athlete ID / media / archive / ParserNews / broadcast.
- Транспорт продуктовой аналитики (согласие уже пишется).

## Следующий P0 (owner)

1. SMTP владельца (см. `OWNER_COMMANDS.md`)
2. Поднять staging на VPS (см. `STAGING.md`) и записать evidence в CURRENT_STATE
3. Убедиться, что GitHub Actions CI зелёный на `main`

## Следующий P0 (код, незаблокированный)

1. Document upload API организатора  
2. Event checklist в Event App  
3. Модель Heat / StartList / Run

## Проверки

- `npm run reseed` — seed Form Excel + restart API
- `pytest` в `services/api`: **36 passed** (Python 3.11)
- Smoke: `/health`, `/login`, `/register`, `/legal/terms_of_use`, `/events/1`, `/profile`, `/notifications`

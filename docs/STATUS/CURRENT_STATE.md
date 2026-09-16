# CURRENT_STATE

Дата: 2026-09-16  
Версия продукта: **0.5.10** + **Champ App UX/UI 1.0 foundation** (ветка `cursor/p0-import-center-athlete-link`)  
Путь до DoD v1 (аудит): ~**86%** — identity + import + транскрипт Казани + **roster lock / chief-judge publish**; полевой dry-run и homologation на реальном старте ещё не закрыты. UX-итерация начата (канон + Quick Wins), role modes Athlete/Judge/Control Room — в работе по PR-плану. Каталог выдачи приложения — в Event App, нативных APK/IPA **нет**.

Сверка с journeys: [ROLE_JOURNEYS_RECONCILIATION.md](./ROLE_JOURNEYS_RECONCILIATION.md).  
UX/UI канон: [UX_UI_CANON.md](../PRODUCT/UX_UI_CANON.md).  
Сверка с прикреплёнными DOCX: [GAP_VS_ATTACHED_DOCS.md](./GAP_VS_ATTACHED_DOCS.md) — **не всё из экосистемы/Hub относится к этому репо**.

## Staging (remote)

- Host: Timeweb VPS `62.113.42.227` (`mywave-bot-server`), каталог `/var/www/mywave-event-app` — отдельно от ботов.
- Стек: `docker compose -f docker-compose.staging.yml`, `APP_ENV=staging`.
- Web: http://62.113.42.227:3001 — HTTP 200 (2026-09-15T14:50Z).
- API health: `{"status":"ok","app":"MyWave Event App (Staging)","env":"staging","db_ok":true}`.
- `GET /api/v1/roles` включает `chief_judge` (10 ролей) — образ **0.5.9** поднят.
- Гость: `GET /api/v1/events` → `total: 0` — оба события в **`draft`**, витрина их скрывает. Внутри БД (2026-09-15T15:03Z): event 1 Казань + event 2 «Всероссийские…», **40 heats / 110 draft results**, roster не lock. Backup: `/var/backups/mywave-event-app/mywave_event_staging.20260915T150340Z.db` (580K).
- SMTP нет — OTP в mail_outbox.
- Это **не** production. Production не менялся.

## Работает

- Remote + CI + release + staging runbook.
- Auth / roles / consent / notifications / applications / roster / training slots.
- Documents, checklist, heats / start list / runs.
- Results draft → verified → **published только chief_judge** (0.5.9).
- Roster lock: фиксирует состав; check-in и судейство остаются.
- Rules catalog + EventRulesProfile (FVLS/IWWF).
- ProtocolCapture (фото/PDF); publish протокола — chief_judge.
- Structured scoring, official protocol export, Athlete ID, archive lock.
- **UX 0.5.6–0.5.7:** публичная витрина, светлая тема, закрытые ролевые пути.
- **0.5.8:** AthleteProfile + Import Center + pending_claim. ADR-0007 **accepted**.
- Транскрипт бумажных протоколов Казани + места ФВЛС 15.08.2026 в **draft**. Не homologated → не публикуется автоматически. Площадка: оз. Нижний Кабан.
- **0.5.9:** ADR-0008 roster lock + chief_judge; journeys в `docs/PRODUCT/journeys/`.
- **Champ App UX/UI 1.0 (foundation):** `UX_UI_CANON.md`; Russian-only UI в AGENTS/PRD; Events (Идёт сейчас / Ближайшие / Мои / Архив); nearest event; mobile bottom nav без «Выйти»; notifications deep-link; live heat primary CTA + `•••`; «Следующий шаг» на карточке события; Field foundation; user-facing ошибки без «API/dev».
- **0.5.10:** карточка выдачи MyWave Event App в «Проекты → Чек-лист организатора» и на вкладке подготовки события. API `app-downloads` + analytics ingest. Android/iOS/source **не подключены**. Документация установки bundled. ADR-0009.

## Частично / нет

- Полные role modes: Athlete Event Home, Organizer Control Room, Judge current-athlete, Broadcast — по PR 3–6 плана UX 1.0
- Казань: нет баллов части финалов и части квалиф.; O40 только пьедестал WB boat men
- Commentator / photographer / EXIF / ParserNews / volunteer / boat captain / broadcast
- PDF protocol export
- SMTP — owner
- Telegram/MAX/native — не Stage 1 этого репо
- Native iOS/Android — нет (PWA)
- Полевой dry-run судья+организатор+chief на площадке — не выполнен
- PR #2 в `main` не влит (`main` = 0.5.7)
- В логе деплоя 0.5.9 сначала не было копии SQLite; backup сделан 2026-09-15T15:03Z (580K). Данные Казани не потеряны.

## Следующий P0

1. PR-план UX 1.0: Athlete Event Home → Organizer Control Room → Live Heat polish → Judge Mode.
2. По желанию владельца: статус **карточки** Казани `draft` → `published` или `live` (витрина). Результаты не публиковать.
3. Roster lock на Казани, когда состав проверен. Official publish — только `chief_judge`.
4. SMTP на staging.
5. Медиа/эфир/волонтёры — после стабилизации scoring/publish.

## Проверки

- pytest: **104 passed** (каталог выдачи 0.5.10)
- tsc: **passed**
- lint (next lint): **passed**, без warning
- production build web: **passed** (маршрут `/projects/checklist-org` в выдаче)
- smoke staging 0.5.9: health + roles + web 200; БД: 2 draft events, 40 heats, 110 draft results; backup 20260915T150340Z

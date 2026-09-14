# CURRENT_STATE

Дата: 2026-09-15  
Версия продукта: **0.5.9** (ветка `cursor/p0-import-center-athlete-link`; tag после merge)  
Путь до DoD v1 (аудит): ~**86%** — identity + import + транскрипт Казани + **roster lock / chief-judge publish**; полевой dry-run и homologation на реальном старте ещё не закрыты.

Сверка с journeys: [ROLE_JOURNEYS_RECONCILIATION.md](./ROLE_JOURNEYS_RECONCILIATION.md).  
Сверка с прикреплёнными DOCX: [GAP_VS_ATTACHED_DOCS.md](./GAP_VS_ATTACHED_DOCS.md) — **не всё из экосистемы/Hub относится к этому репо**.

## Staging (remote)

- Host: Timeweb VPS `62.113.42.227` (`mywave-bot-server`), каталог `/var/www/mywave-event-app` — отдельно от ботов.
- Стек: `docker compose -f docker-compose.staging.yml`, `APP_ENV=staging`.
- Web: http://62.113.42.227:3001
- API: http://62.113.42.227:8001
- На сервере после 0.5.8 ingest (2026-09-02): событие id=1 «Чемпионат России в Казани 2026» — **40 heats / 173 старта / 110 draft results**. Гость unpublished не видит.
- SMTP нет — OTP в mail_outbox.
- Это **не** production. Production не менялся.
- **0.5.9 на staging ещё не задеплоен**, пока не собран новый образ с roster lock / `chief_judge`.

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

## Частично / нет

- Казань: нет баллов части финалов и части квалиф.; O40 только пьедестал WB boat men
- Commentator / photographer / EXIF / ParserNews / volunteer / boat captain / broadcast
- PDF protocol export
- SMTP — owner
- Telegram/MAX/native — не Stage 1 этого репо
- Native iOS/Android — нет (PWA)
- Полевой dry-run судья+организатор+chief на площадке — не выполнен
- PR #2 в `main` не влит (`main` = 0.5.7)

## Следующий P0

1. Deploy 0.5.9 на staging (backup SQLite → rebuild). Назначить пользователя `chief_judge` на Казань, если нужно публиковать.
2. Не публиковать Казань, пока нет homologation / решения владельца.
3. SMTP на staging.
4. Медиа/эфир/волонтёры — после стабилизации scoring/publish.

## Проверки

- pytest: P0 roster lock + chief publish + прежние suites (см. VALIDATION_REPORT)
- UI lock / «Ждёт главного судью» — после staging deploy 0.5.9

# CURRENT_STATE

Дата: 2026-08-30  
Версия продукта: **0.5.8** (ветка `cursor/p0-import-center-athlete-link`; tag после merge)  
Путь до DoD v1 (аудит): ~**82%** — identity + import staging есть; live scoring path ещё не закрыт на реальном старте.

Сверка с прикреплёнными DOCX: [GAP_VS_ATTACHED_DOCS.md](./GAP_VS_ATTACHED_DOCS.md) — **не всё из экосистемы/Hub относится к этому репо**.

## Staging (remote)

- Host: Timeweb VPS `62.113.42.227` (`mywave-bot-server`), каталог `/var/www/mywave-event-app` — отдельно от ботов.
- Стек: `docker compose -f docker-compose.staging.yml`, `APP_ENV=staging`.
- Web: http://62.113.42.227:3001 — HTTP 200.
- API health: `{"status":"ok","app":"MyWave Event App (Staging)","env":"staging","db_ok":true}` (2026-08-30T04:10:27Z).
- На сервере до обновления 0.5.8: **v0.5.7** / SHA `ebb43b7`, пустая SQLite, без seed Казани. SMTP нет — OTP в mail_outbox.
- Это **не** production. Production не менялся.

## Работает

- Remote + CI + release + staging runbook.
- Auth / roles / consent / notifications / applications / roster / training slots.
- Documents, checklist, heats / start list / runs.
- Results draft → verified → published → void.
- Rules catalog + EventRulesProfile (FVLS/IWWF).
- ProtocolCapture (фото/PDF).
- Structured scoring, official protocol export, Athlete ID, archive lock.
- **UX 0.5.6–0.5.7:** публичная витрина, светлая тема, закрытые ролевые пути.
- **0.5.8:** AthleteProfile + Import Center + pending_claim + маскировка телефонов в preview. Канон категорий Казани **не** зафиксирован (ADR-0007).

## Частично / нет

- Казань-2026 в staging roster — после деплоя 0.5.8 и загрузки xlsx владельцем (файлы с Desktop, не из git)
- Start lists / heats / scoring на реальных данных Казани
- Commentator / photographer / EXIF / ParserNews
- PDF protocol export
- SMTP — owner
- Telegram/MAX/native — не Stage 1 этого репо
- Native iOS/Android — нет (PWA)
- Полевой dry-run судья+организатор на площадке — не выполнен

## Следующий P0 (после деплоя import)

1. Владелец подтверждает категории (ADR-0007), затем officials + event prep
2. Start lists → check-in → scoring на пилотном событии
3. SMTP на staging

## Проверки

- pytest: import center + pending_claim + restricted documents (см. VALIDATION_REPORT)
- UI Import Center / claim — после staging deploy, browser smoke владельцем


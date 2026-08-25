# CURRENT_STATE

Дата: 2026-08-25  
Версия продукта: **0.5.2**  
Путь до DoD v1 (аудит): ~**52%**

## Работает

- Remote + CI + release discipline + staging runbook (Этап 0).
- Auth / roles / consent / notifications / applications / roster / training slots.
- Document upload/delete организатора.
- Event checklist в Event App (SoT не на сайте).
- Heats / start list / run + статусы day-of.
- Bulk fill start list из roster/category.
- Results draft → verified → published → void + history.
- **Rules catalog** (`GET /api/v1/rules/catalog`) — FVLS/IWWF, P0 дисциплины, packs.
- **EventRulesProfile** при создании события и `PUT .../rules-profile`.
- **ProtocolCapture** — фото/PDF листа судьи, upload (organizer+/judge), verify → publish, audit.
- UI: wizard `/events/new`, вкладка «Протокол» на карточке события.

## Частично

- Structured scoring engines (WSWS DRIVE, IWWF T+I, IWWF E/I/C) — каталог есть, расчёт нет.
- Official protocol PDF export — нет (есть capture + verify).
- Athlete ID / media / archive / ParserNews / broadcast — нет.
- SMTP и remote staging host — owner.

## Следующий P0 (код)

1. Scoring engines по `rules_catalog` (WSWS_DRIVE, IWWF_CABLE_TI, IWWF_BOAT_EIC)
2. Official protocol PDF/JSON export из verified captures + results
3. Athlete ID (без PII в идентификаторе)

## Следующий P0 (owner)

1. SMTP
2. Staging на VPS + `npm run reseed` после pull 0.5.x
3. Прогон одного mock competition day на staging

## Проверки

- pytest: **46 passed** (protocol + rules + competition day)
- UI: вкладки Checklist / Docs / **Протокол** / Heats / Results; wizard создания события

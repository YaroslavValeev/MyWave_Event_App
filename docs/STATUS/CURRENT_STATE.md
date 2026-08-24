# CURRENT_STATE

Дата: 2026-08-24  
Версия продукта: **0.5.1**  
Путь до DoD v1 (аудит): ~**48%**

## Работает

- Remote + CI + release discipline + staging runbook (Этап 0).
- Auth / roles / consent / notifications / applications / roster / training slots.
- Document upload/delete организатора.
- Event checklist в Event App (SoT не на сайте).
- Heats / start list / run + статусы day-of.
- Bulk fill start list из roster/category.
- Results draft → verified → published → void + history.

## Частично

- Judge multi-score / calculation engine — нет (только ручной score/place).
- Official protocol PDF export — нет.
- Athlete ID / media / archive / ParserNews / broadcast — нет.
- SMTP и remote staging host — owner.

## Следующий P0 (код)

1. Judge scoring input + aggregation
2. Official protocol export
3. Athlete ID (без PII в идентификаторе)

## Следующий P0 (owner)

1. SMTP
2. Staging на VPS + `npm run reseed` после pull 0.5.x
3. Прогон одного mock competition day на staging

## Проверки

- pytest: цель ≥41 passed (competition day + results)
- UI: вкладки Checklist / Docs / Heats / Results

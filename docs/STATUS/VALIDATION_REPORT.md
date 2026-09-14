# Validation Report — 0.5.9 Roster lock / chief judge

Дата: 2026-09-15  
Продукт: standalone MyWave Event App  
Цикл: P0 vertical slice `roster lock → check-in → draft/verify → chief publish` (ADR-0008)

## Проверки

| Проверка | Результат |
|----------|-----------|
| lint (ruff) | unavailable (не подключён в репо) |
| typecheck web (`tsc --noEmit`) | **passed** (2026-09-15, после правки JSX вкладки результатов) |
| unit/integration pytest | **80 passed** (включая `test_p0_roster_chief.py` + `GET /api/v1/roles`) |
| migrations | SQLite `create_all` + `_ensure_sqlite_columns` для `roster_locked_at` |
| web production build | не запускался в этом цикле |
| security (негативные permission) | organizer/judge **403** `chief_approval_required` на publish; participant **403** на lock; guest не видит draft |
| accessibility | unavailable (axe/e2e не запускались) |
| smoke staging 0.5.9 | **не выполнен** — образ 0.5.9 ещё не задеплоен |
| Docker build | not run this cycle |
| Production deploy | **not performed** |

Не отмечено passed то, что не запускалось.

## Поведение P0

- Lock пустого состава → `400 roster_empty`
- После lock: заявка/accept/import commit → `409 roster_locked`; start-list check-in работает
- Unlock идемпотентен; archive → `409 event_archived`
- Official publish: только `chief_judge` / `platform_admin`

## Казань staging (факт 0.5.8 ingest, 2026-09-02)

40 heats / 173 старта / 110 draft results на event_id=1. Не published. 0.5.9 не меняет эти строки, пока chief не утвердит.

## Оставшиеся блокеры

- Deploy 0.5.9 на staging + backup SQLite
- PR #2 не влит в `main`
- SMTP, полевой dry-run, homologator, медиа/эфир

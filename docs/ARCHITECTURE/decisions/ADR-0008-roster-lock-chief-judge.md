# ADR-0008 — Roster lock и публикация главным судьёй

**Дата:** 2026-09-15  
**Статус:** accepted (P0 vertical slice брифа 14.09.2026)

## Контекст

Целевые journeys требуют maker-checker:

`ввод → проверка → утверждение chief judge → publish → archive`.

До 0.5.8 организатор мог и ввести черновик, и опубликовать официальный результат. Отдельной фиксации состава не было: заявки и Import Center можно было менять во время стартов.

Полная state machine journeys (`configured → roster_locked → … → archived`) ломает существующие статусы события (`draft | published | registration_open | live | completed | cancelled`). Их не расширяем в этом цикле.

## Решение

1. **Roster lock** — отдельный флаг события, не новый `Event.status`:
   - `Event.roster_locked_at`, `Event.roster_locked_by_user_id`
   - `POST /api/v1/events/{id}/roster/lock` и `/unlock` (organizer+)
   - lock идемпотентен; пустой состав → `400 roster_empty`
   - при lock: новые заявки, accept, import commit, ingest-pack, scan-protocol → `409 roster_locked`
   - check-in, heats, scoring, draft results — разрешены
2. **Роль `chief_judge`** в том же enum, что и остальные Stage 1 роли (не отдельная таблица membership).
3. **Публикация official result / protocol capture `published` / void опубликованного** — только `chief_judge` или `platform_admin`. Код ошибки: `chief_approval_required`.
4. Организатор по-прежнему делает draft и `verified`.
5. `platform_admin` — аварийный обход с audit, не замена главного судьи на площадке.

## Последствия

- Существующие тесты, где организатор публиковал результат, переведены на `chief_judge`.
- Казань-2026 на staging остаётся в **draft**, пока главный судья не утвердит (Not homologated по-прежнему не auto-publish).
- Homologator, waitlist, платежи, медиа/эфир — не в этом ADR.

## Откат

Убрать RBAC-гейт в `result_service.transition_result` / `protocol_service` и колонки lock через SQLite ALTER нельзя «вниз»; откат = предыдущий образ API. Колонки nullable, старые клиенты их игнорируют.

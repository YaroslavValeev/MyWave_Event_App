# ADR-0015 — Role-Based Journey Guidance

Дата: 2026-11-04  
Статус: accepted  
Связь: checklist, role_physical_actions, EventStatus, ADR-0013

## Контекст

Нужен экран «Что делать дальше?» без второго workflow-движка.

## Решение

1. **Не** заменять `EventStatus` (`draft|published|registration_open|live|completed|cancelled`).
2. Добавить **вычисляемый** `journey_phase` для UI/guidance:
   `DRAFT → CONFIGURED → REGISTRATION → READY → LIVE → RESULTS_REVIEW → OFFICIAL → ARCHIVED`.
3. Endpoint `GET /api/v1/events/{id}/guidance` собирает задачи из:
   - checklist items;
   - role-actions (справочник);
   - статусов applications / results / publications (по роли).
4. Клиент может скрыть рекомендательные подсказки (`localStorage`); обязательные остаются видимыми.
5. Offline: показывать только локально известные шаги; серверные шаги помечать `requires_online`.

## Последствия

Guidance — presentation layer над SoT API. Не создаёт параллельный task store.

# CURRENT_STATE

Дата: 2026-08-24  
Версия продукта: **0.5.0**  
Путь до DoD v1 (аудит): ~**42%** (было ~32%; закрыт prep gap upload/checklist + foundation heats)

## Работает

- Standalone продукт `MyWave_Event_App` (не плагин сайта).
- Git remote: https://github.com/YaroslavValeev/MyWave_Event_App (private); tag `v0.4.0`; CI зелёный.
- Phone auth, роли, consent, notifications, applications, roster, training slots.
- **Document upload/delete** организатором (`POST/DELETE .../documents`).
- **Event checklist** в Event App (`GET/PATCH .../checklist`) — сайт не SoT.
- **Heats / start list / run** foundation API + UI вкладка Heats.
- Seed Казань 2026 (Form Excel).
- Staging runbook + compose; release discipline.

## Частично

- Heats: CRUD + статусы есть; нет массовой генерации start list из roster, judge scoring, published results.
- OTP/approve без SMTP → outbox.
- Staging compose готов; remote VPS ещё нет.

## Отсутствует

- Production SMTP; remote staging evidence.
- Results / protocols / Athlete ID / media / archive / ParserNews / broadcast.
- Judge input + calculation + draft/verify/publish.

## Следующий P0 (owner)

1. SMTP
2. Staging на VPS
3. `npm run reseed` после обновления API (новые таблицы create_all)

## Следующий P0 (код)

1. Bulk fill start list из roster/category
2. Results draft → verify → publish + audit
3. Athlete ID (без PII в самом ID)

## Проверки

- `pytest` в `services/api`: **40 passed**
- Smoke: `/events/[id]` → Чеклист, Документы (upload), Heats

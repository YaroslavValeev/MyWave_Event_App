# ROADMAP — Competition Platform (v1)

Дата: 2026-08-24  
Цель: провести **одно реальное соревнование** end-to-end без Excel как Source of Truth.

Оценка аудита (вход): ~**32%** пути до DoD v1.

## Definition of Done v1

Минимум одно соревнование проходит полностью:

**подготовка → регистрация → check-in → heats → scoring → results → official protocol → archive**

без Excel как основного SoT.

---

## Этап 0 — Git / repository (P0 сейчас)

| # | Задача | Статус |
|---|--------|--------|
| 0.1 | Commit `0.4.0` + tag `v0.4.0` | **done** |
| 0.2 | Remote (GitHub) — единственная рабочая история не на локальном диске | **done** (`YaroslavValeev/MyWave_Event_App`, private) |
| 0.3 | CI на push/PR (pytest + Next build) | done |
| 0.4 | Release discipline (semver, tag, CHANGELOG, rollback) | **done** |
| 0.5 | Staging environment (compose + runbook) | **done** (remote host — owner) |

## Этап 1 — Event preparation

Довести в **Event App** (сайт = витрина/вход, не SoT чеклиста):

- upload документов организатором
- checklist внутри Event App
- categories (нормализация)
- officials
- approvals
- registration
- roster

Частично уже есть: event, роли, заявки, roster, seed docs, training slots, notifications.

## Этап 2 — День старта (главный функциональный разрыв)

Сущности:

- Heat
- Start list
- Run
- Participant order
- Status (DNS / DNF / check-in / ready / on-water / completed)

Training slots ≠ competition heats.

## Этап 3 — Results

- judge input
- calculation
- draft result
- verification
- published result
- official protocol
- history / audit после публикации

## Этап 4 — Athlete ID

Постоянный **MyWave Athlete ID** без ФИО/телефона/PII в самом ID.

Связывает: profile, events, categories, results, start history, media, future coaching/training.

## Этап 5 — Media / Photographer Mode

После стабилизации start/results:

- текущий heat, фото, имя, номер, Athlete ID, фактическое время выхода
- EXIF/timecode ↔ интервал выступления
- спортсмен видит свои медиа без ручного поиска

## Этап 6 — Archive

После `completed` → read-only архив: roster, heats, protocols, results, media, Athlete IDs, документы.

## Этап 7 — ParserNews / Content Engine

Published result → ParserNews → draft article → Owner commentary → publication.

## Этап 8 — Broadcast / commentator

Только после работающего scoring/results: profile, прошлые результаты, achievements, heat, tricks, media, stats.

---

## Каналы (не путать с этапами продукта)

| Канал | Когда |
|-------|--------|
| Web/PWA | сейчас (основной UI) |
| Telegram / MAX adapters | после Этапа 1–2 стабилизации |
| Capacitor Android/iOS | после Live Competition basics |
| Site MyWave | витрина / Download Center, не SoT |

## Owner blockers (вне кода)

1. Production SMTP (Gmail App Password)
2. Создание/доступ к GitHub remote + push
3. Hosting для staging (VPS / container host)

## Следующий код P0 (после Этапа 0)

1. Document upload API организатора
2. Event checklist в Event App
3. Модель Heat / StartList / Run (Этап 2)

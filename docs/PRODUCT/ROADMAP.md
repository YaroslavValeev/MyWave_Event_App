# ROADMAP — Competition Platform (v1)

Дата: 2026-10-27  
Цель: провести **одно реальное соревнование** end-to-end без Excel как Source of Truth.

Оценка пути до DoD v1: ~**80%** (ядро Stage 1 в коде; блокер — пилот на площадке).

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

| Задача | Статус |
|--------|--------|
| upload документов | **done (0.5.0)** |
| checklist в Event App | **done (0.5.0)** |
| categories / officials / approvals / registration / roster | **done для пилота** (seed + API + UI; полный CRUD категорий — polish) |

## Этап 2 — День старта

| Задача | Статус |
|--------|--------|
| Heat / StartList / Run foundation | **done (0.5.0)** |
| bulk start list | **done (0.5.1)** |
| DNS/DNF labels | **done (0.5.5)** |
| live board polish | next (не блокер пилота) |
| Results scoring | **done (0.5.3)** engines + judge sheets + aggregate |
| Official protocol export | **partial (0.5.4)** JSON + HTML; PDF optional |

## Этап 3 — Results

- judge input — **done (0.5.3)**
- calculation — **done (0.5.3)**
- draft result — **done**
- verification — **done**
- published result — **done**
- official protocol — **partial (0.5.4)** JSON/HTML
- history / audit после публикации — **done**

## Этап 4 — Athlete ID

Постоянный **MyWave Athlete ID** без ФИО/телефона/PII в самом ID. — **done (0.5.5)** `MW-XXXXXXXX`

Связывает: profile, events, categories, results, start history, media, future coaching/training.

## Этап 5 — Media / Photographer Mode

После стабилизации start/results:

- текущий heat, фото, имя, номер, Athlete ID, фактическое время выхода
- EXIF/timecode ↔ интервал выступления
- спортсмен видит свои медиа без ручного поиска

## Этап 6 — Archive

После `completed` → read-only архив: roster, heats, protocols, results, media, Athlete IDs, документы. — **done (0.5.5)** (media ещё нет)

## Этап 6.5 — Event reporting (канон 2026-10-27)

Dual-track: Live ops + sparse moments + EventReport draft (template → optional LLM) + human publish.  
Docs: `EVENT_REPORTING_MODEL.md`, ADR-0012, виртуальный прогон Казани.  
Код 0.5.8: assemble/publish template без LLM; STT/LLM — feature flags.

## Этап 7 — ParserNews / Content Engine

Published **EventReport** (+ published results) → ParserNews → draft article → Owner commentary → publication.

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

1. **Pilot dry-run** судья + организатор на одном событии (закрывает DoD v1)
2. Production SMTP (Gmail App Password или аналог)
3. Hosting для staging (VPS / container host) — compose/runbook уже есть
4. ~~GitHub remote + push~~ **done**

## Следующий P0 (2026-10-27)

1. Pilot dry-run E2E: подготовка → регистрация → check-in → heats → scoring → results → protocol → archive
2. SMTP + staging host (owner)
3. EventReport UI + day-of checklist; deep-link / PDF / live board — polish
4. Этапы 5–8 (Media, Archive media, ParserNews, Broadcast) — **после** стабильного дня старта

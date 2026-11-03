# Champ App — программа модернизации (Orchestrator)

Дата: 2026-11-03  
Репозиторий: локальный checkout `MyWave_Event_App`  
Версия после работ этой сессии: **0.5.16** (публикации + лента)

Документ фиксирует **факт** аудита и реализации. Не выдаёт симуляцию за тест на Xiaomi 14 и не заявляет APK без артефакта.

## Раздел 1. PROJECT AUDIT (факт)

| Компонент | Технология | Состояние |
|-----------|------------|-----------|
| Frontend | Next.js 15 / React 19 / TS | есть |
| Backend | FastAPI / SQLAlchemy | есть |
| DB | SQLite (+ Postgres optional) | есть |
| Auth | JWT + phone OTP | есть |
| Роли | enum в `domain/roles.py` | есть |
| EventReport / ProtocolCapture | отдельные домены | есть |
| Publication feed | ADR-0013 | **добавлено 0.5.16** |
| Offline MVP | OFFLINE_SYNC Stage 3 | нет; локальные черновики ленты — да |
| Native Android APK | Capacitor | **нет** |
| PWA | manifest-only | есть |

Baseline pytest до изменений: **67 passed**.

Роли в коде: `participant`, `organizer`, `judge`, `commentator`, `media`, `support`, `federation_manager`, `event_admin`, `platform_admin`.  
Документ `USER_ROLES_AND_JOURNEYS.md` содержит устаревшие имена (`athlete`, `registrar`) — не дублировать в API.

## Раздел 2. MULTI-AGENT TEAM

| Агент | Статус в сессии |
|-------|-----------------|
| 01 Orchestrator | активен |
| 02 Auditor | выполнен (explore) |
| 03 UI/UX | частичный (лента + токены) |
| 04 RBAC | выполнен (publication_policy) |
| 05 Content | выполнен (API + UI) |
| 06 Offline | частичный (localStorage drafts; без auto-flush очереди) |
| 07 QA | API tests publications; E2E NOT RUN |
| 08 Android | ADR-0014; APK BLOCKED |
| 09 Security | magic-bytes media; role mismatch 403 |
| 10 Release | чек-лист Xiaomi 14 |

## Раздел 3. EXECUTION ROADMAP

| Этап | Статус |
|------|--------|
| A Аудит | DONE |
| B Контракты / ADR | DONE |
| C Разработка публикаций | DONE (MVP) |
| D Интеграция | DONE локально |
| E QA full matrix | PARTIAL |
| F Fix | ongoing |
| G Android APK | BLOCKED |
| H Xiaomi device | NOT RUN |

## Раздел 4. BACKLOG (актуальный)

| ID | Pri | Статус | Задача |
|----|-----|--------|--------|
| AUD-01 | P0 | DONE | инвентаризация |
| SEC-01 | P0 | DONE | RBAC публикаций + тесты |
| API-01…04 | P1 | DONE | контракт + CRUD + media |
| UI-03 | P1 | DONE | лента / редактор |
| OFF-01 | P1 | DONE | local drafts |
| OFF-02 | P1 | PARTIAL | idempotency сервер есть; auto-queue flush нет |
| QA-02 | P1 | TODO | Playwright E2E |
| AND-03 | P1 | BLOCKED | debug APK |
| REL-01 | P1 | DONE | Xiaomi checklist doc |
| UI-01 | P2 | TODO | полный дизайн-аудит всех экранов |
| OFF-03 | P2 | TODO | конфликт-синк |

## Раздел 5–9

См. итоговый отчёт Orchestrator в чате владельца и:

- ADR-0013 / ADR-0014
- `docs/OPERATIONS/XIAOMI14_TEST_CHECKLIST.md`
- `docs/STATUS/CURRENT_STATE.md` / `CHANGELOG.md`

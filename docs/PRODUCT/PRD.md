# PRD — MyWave Event App

Статус: канонический (Этап 1 + consent + Champ App UX/UI 1.0)  
Дата: 2026-09-15  
Владелец: MyWave

## Проблема

Организаторам и участникам соревнований нужен единый цифровой контур события: роли, программа, документы, уведомления и live-режимы — как **самостоятельное приложение**, а не как раздел чужого сайта или чат-бота.

## Продукт

**MyWave Event App** — standalone цифровая платформа соревнований.  
Альтернативное документационное имя: `FVLS × MyWave Competition Hub` (не переименовывать код без решения владельца).  
Рабочее имя продуктовой итерации UI: **Champ App** (UX/UI 1.0 — Role Based + Live First).

## UX / Product principles

- интерфейс **Russian-only**;
- **Role Based** — разные presentation experiences при общей модели данных;
- **Live First** — текущий заезд, текущий спортсмен, «требует внимания»;
- **task-first**, а не module-first;
- **mobile-first**;
- API/DB остаются Source of Truth;
- live-operation safety важнее визуальных эффектов;
- не переписывать рабочий backend ради redesign без необходимости.

Канон деталей: [UX_UI_CANON.md](./UX_UI_CANON.md).

## Пользователи

participant, organizer, judge, chief_judge, commentator, media, support, federation_manager, event_admin, platform_admin.

## Цели Этапа 1

1. Воспроизводимый local/server setup.
2. Единое API-ядро health + auth/roles + events.
3. Web/PWA shell.
4. Audit foundation.
5. Каноническая документация.

## Scope Этапа 1 (сейчас)

- FastAPI backend.
- Next.js PWA shell (hero, login, register+consent, events, profile, health).
- SQLite локально / PostgreSQL-ready URL.
- Phone OTP + role approval; dev-login только в development/test.
- RBAC foundation на событиях.
- Self-serve заявки и минимальные согласия.

## Out of scope сейчас

- Подписанные APK/IPA.
- Capacitor/offline production.
- Telegram/MAX как ядро UX.
- Live judge/commentator full mode.
- Медиа-хранилище full workflow (EXIF, альбом спортсмена). **Срез 1:** FieldMoment — камера PWA для команды события (ADR-0011).
- Consent full workflow (экспорт/удаление субъекта) — **минимальный grant/revoke Stage 1 есть** (ADR-0004).

## Acceptance (foundation)

- `/health` и `/ready` работают.
- Dev-login выдаёт JWT и `/api/v1/me`.
- Organizer создаёт событие; participant не может.
- Audit фиксирует login/create/update.
- Web открывает бренд, вход, список событий.
- Download Center лежит в `releases/` и не является ядром.

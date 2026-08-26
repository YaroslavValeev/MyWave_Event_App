# Changelog

## 0.5.4 — 2026-08-26

- Official protocol export: JSON bundle + download + printable HTML.
- Readiness check: FVLS/IWWF + published results or protocol captures.
- UI: кнопки «Скачать JSON» / «Печатная HTML» на вкладке «Протокол».
- Pytest: **52 passed**.

## 0.5.3 — 2026-08-25

- Structured scoring engines: WSWS_DRIVE, IWWF_CABLE_TI, IWWF_BOAT_EIC (+ MANUAL_PLACE meta).
- JudgeScore API: submit sheet, list, aggregate panel → result draft.
- UI: вкладка «Судейство» на карточке события.
- Gap-анализ vs прикреплённые DOCX экосистемы / Production Hub.
- UX create event: даты, авто-slug, чекбоксы дисциплин.

## 0.5.2 — 2026-08-25

- Rules catalog API: governing bodies, P0 disciplines, rules packs, scoring modes.
- EventRulesProfile: FVLS + IWWF sanction, discipline codes, scoring mode (create + upsert).
- ProtocolCapture: upload JPG/PNG/WebP/PDF (organizer+/judge), verify → publish, file download.
- UI: wizard `/events/new` (дисциплины + режим протокола), вкладка «Протокол».
- ADR-0006 governing bodies / scoring profiles (draft).
- Pytest: **46 passed**.

## 0.5.1 — 2026-08-24

- Bulk fill start list из roster/category (`POST .../start-list/fill`).
- Results foundation: draft → verified → published → void + `result_history` audit.
- UI: «Заполнить из roster», вкладка Results.

## 0.5.0 — 2026-08-24

- Document upload/delete организатора (PDF/XLSX/XLS, ≤25 МБ, audit).
- Event checklist внутри Event App (auto-seed + auto-tick по данным).
- Foundation дня старта: Heat, StartListEntry, Run + статусы check-in/DNS/DNF/on-water.
- UI: вкладки Чеклист / Документы (upload) / Heats.
- Pytest: **40 passed**.

## 0.4.0 — 2026-08-24

- Email-ссылки approve/reject больше не меняют статус по GET: нужна POST-форма подтверждения (ADR-0005).
- Очередь ролей в API не отдаёт raw token; UI утверждает по `approval_id`.
- In-app журнал уведомлений: заявка/роль видны в `/notifications` без SMTP.
- Лимит OTP: 5 запросов на номер за 10 минут.
- Production отказывается стартовать с дефолтным/коротким `SECRET_KEY`.
- Удалены неиспользуемые `app/schemas.py` и `app/services/core.py`.
- Версии синхронизированы до `0.4.0` (root/web/api).
- Release discipline + staging runbook (`RELEASE.md`, `STAGING.md`, `docker-compose.staging.yml`, workflow `release.yml`).
- Roadmap: Competition Platform DoD v1 (подготовка → archive без Excel SoT).
- Pytest: **36 passed**. Next.js build: passed (в т.ч. `/notifications`).

## 0.3.0 — 2026-08-24

- Минимальный контур согласий Stage 1: `ConsentRecord`, каталог `docs/LEGAL/*`, публичный API документов.
- Регистрация требует `terms_of_use` и `privacy_policy`; опционально публикация имени и аналитика.
- Профиль: просмотр/выдача/отзыв опциональных согласий; обязательные нельзя отозвать.
- Публичный roster маскирует ФИО self-serve заявок без publish-consent (`Участник №id`); импорт организатора без изменений.
- Audit: `consent.granted` / `consent.revoked`.
- ADR-0004. Pytest: 29 passed.

## 0.2.0 — 2026-08-05

- Домен соревнования: категории, участники, документы.
- Seed ЧР/ПР Казань 2026 из Excel/PDF организатора (без телефонов/медссылок).
- UI карточки события `/events/[id]`.
- `npm run dev` — однокомандный локальный запуск.

## 0.1.0 — 2026-08-04

- Инициализация standalone-репозитория MyWave Event App.
- Архивация Download Center в `releases/download-center-2026-08-02/`.
- Stage 1 API: health/ready, JWT dev-login, roles, events, audit.
- Stage 1 Web/PWA shell.
- Канонические документы и серверные команды.

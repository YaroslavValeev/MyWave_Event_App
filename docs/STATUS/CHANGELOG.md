# Changelog

## 0.5.12 — 2026-09-18 (код, staging после выката 0.5.11)

- Страница `/projects/checklist-org`: интерактивный справочник площадки — **11 разделов** (судьи, акватория, зоны, медиа, партнёры). Отметки в браузере, не в протоколе события.
- Вкладка «Подготовка» события ссылается на этот справочник. Операционный чеклист события (документы/состав/старты) не заменён.

## 0.5.11 — 2026-09-17 (git `46a23b4`, staging ещё 0.5.10 до выката)

- FieldMoment: фото/видео с камеры телефона (PWA `<input capture>`) для бэкстейджа, взгляда пилота, маршала на старте и других эмоциональных кадров.
- API `GET/POST/PATCH /api/v1/events/{id}/field-moments` + file; роли media/commentator/support/organizer+/chief_judge; участник 403; гость 401.
- Статусы `draft` → `approved` (для эфира) / `withheld`; approve только организатор+ и главный судья.
- UI: вкладка «Моменты», кнопка «Снять момент» на пульте организатора. Не смешивается с ProtocolCapture.
- ADR-0011. EXIF, альбом спортсмена, соцсети, live-превью getUserMedia — не этот срез.

## 0.5.10 — 2026-09-16

- Каталог выдачи MyWave Event App: `/projects/checklist-org#mywave-event-app` и блок на вкладке «Подготовка» события.
- API: `GET /api/v1/app-downloads/manifest|status`, `POST .../handoff` (URL только из env, fail-closed).
- Аналитика: `POST /api/v1/analytics/events` для событий карточки выдачи.
- Плейсхолдеры `{{android_download_url}}`, `{{ios_testflight_url}}`, `{{source_archive_url}}` — нативных сборок нет.
- Документация по установке bundled: `/downloads/install-and-run.html` (без фиктивного APK).
- Документы: ADR-0009, ADR-0010 (JWT localStorage), `docs/OPERATIONS/APP_DOWNLOADS.md`, письмо сайту `docs/INTEGRATIONS/SITE_MYWAVE_DOWNLOAD_HANDOFF.md`.
- План отладки PWA до native: `docs/PRODUCT/QA_AND_UX_HARDENING_PLAN.md`. Письмо сайту уточнено: documentation available, android/ios/source нет, staging на 2026-09-16 ещё 0.5.9.
- Карточка события: «Мой старт» для участника, пульт организатора, судейство текущего спортсмена без длинного dropdown как primary.
- Authz: участник 403 на roster lock и official publish (регресс-тест). Analytics ingest не сохраняет email/phone/token. Upload: empty/oversize/path traversal.

## 0.5.9+ UX/UI 1.0 foundation — 2026-09-15

- Канон: `docs/PRODUCT/UX_UI_CANON.md` (Role Based + Live First + Russian-only UI); обновлены AGENTS, PRD, CANONICAL_DOCS_INDEX, правило frontend.
- Quick Wins: Events → Идёт сейчас / Ближайшие / Мои / Архив; `pickNearestEvent`; mobile nav без «Выйти» (выход в профиле); actionable notifications + deep-link; «Следующий шаг» на event home; live heat/entry — один primary CTA + меню `•••`.
- UI copy: без production-текстов про API/dev/mail_outbox; OTP явно на email; светлые controls вместо тёмных inline-styles; Field foundation.
- Backend: user-facing OTP message без `mail_outbox`.

## 0.5.9 — 2026-09-15

- P0 vertical slice: **roster lock** + публикация official result только **главным судьёй** (ADR-0008).
- Роль `chief_judge`; API `POST .../roster/lock|unlock`; `403 chief_approval_required` если организатор публикует сам.
- Целевые journeys перенесены в `docs/PRODUCT/journeys/`; сверка — `docs/STATUS/ROLE_JOURNEYS_RECONCILIATION.md`.
- Казань на staging по-прежнему draft до утверждения chief judge (Not homologated, без auto-publish).

## 0.5.8 — 2026-08-30

- Import Center: staging xlsx → match/conflicts → commit в `AthleteProfile` + `EventRegistration` (`Participant`). Повтор того же файла идемпотентен.
- MyWave Athlete ID на профиле спортсмена; `pending_claim` аккаунты для известных телефонов; OTP обязателен; подтверждение связи в профиле.
- Документы: `access_class`; medical-restricted скрыт от participant.
- ADR-0007: категории «до 15/до 19» vs U14/U18 — decision required, без молчаливого маппинга.
- UI: `/admin/imports`, пункт «Импорт», подтверждение профилей на `/profile`.
- `GET .../schedule-hint` строится из полей **этого** события; текст бюллетеня Казани (оз. Кабан, 11–16.08) не подставляется в чужие карточки.
- ADR-0007 **accepted**: одно событие ЧР+ПР Казань; канон категорий IWWF U14 / U18 / O30 / O40 / Open (чемпионат). Junior/Grom → U14/U18. Возраст на 31.12.2026.
- `POST /api/v1/events/{id}/ingest-pack` — пакет xlsx+PDF: состав, судьи, start list, документы.
- `POST /api/v1/events/{id}/scan-protocol` — бумажные протоколы Казани + итоги поста ФВЛС 15.08.2026 (места финалов, Мастерс → O30) и пьедестал O40 ветераны вейкборд-катер. Черновики, без автопубликации.
- UI `/admin/imports`: кнопка «Разложить сканы Казани». Фото протоколов и xlsx с телефонами **не** в git.
- Казанские xlsx/pdf с PII **не** в git. Загрузка только на сервер через UI.

## 0.5.7 — 2026-08-27

- Светлая тема: белый/мятный фон, тёмный текст, бирюзовые обводки и тени кнопок.
- Просроченный/битый Bearer на публичных GET не даёт 401: гость видит витрину. Карточка события показывает «Сессия истекла» + «Войти снова» с `?next=`.
- Закрыты тупики ролей: создание события, доступы, профиль, уведомления — вход или понятный отказ, не голый error.
- GET `/heats` доступен гостю на публичных событиях (стартовый список — только с сессией).
- PWA theme_color / иконка под светлую палитру.
- Версия API `__version__` / OpenAPI = 0.5.7. Staging compose передаёт `NEXT_PUBLIC_API_BASE_URL` в Docker build.

## 0.5.6 — 2026-08-27

- Публичная витрина: GET `/api/v1/events`, detail, categories, officials, published results, schedule-hint — без токена (только публичные статусы).
- UI: ролевые вкладки на карточке события; русские статусы (заявка / заезд / результат / протокол).
- Вход: dev-login только `?dev=1` в development. Регистрация — участник по умолчанию, staff по отдельному запросу.
- Навигация: «Доступы» вместо коллизии «Заявки»; `/health` убран из меню; нижняя панель на мобильном.
- Participant не видит «Создать соревнование». После входа — последнее событие.
- Каноническое имя продукта не менялось: MyWave Event App.
- Pytest: **58 passed** (включая публичную витрину).

## 0.5.5 — 2026-08-26

- MyWave Athlete ID (`MW-XXXXXXXX`) на User: выдаётся при register/dev-login/`GET /me`.
- Roster и профиль показывают athlete_id (без PII в самом ID).
- Read-only archive: `completed`/`cancelled` блокируют мутации (409 `event_archived`).
- Escape hatch: `PATCH .../status` (и кнопка «Вернуть в live»).
- UX: DNS/DNF labels на start list; баннер архива.
- Pytest: athlete + archive suite.

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

# CURRENT_STATE

Дата: 2026-09-22  
Версия продукта: **0.5.13 на staging** (git `7795deb`) — вход по телефону без OTP, пока SMTP не настроен. Каталог выдачи в manifest по-прежнему подписан **0.5.10** (документация; android/ios недоступны).  
Путь до DoD v1 (аудит): ~**86%** — identity + import + транскрипт Казани + **roster lock / chief-judge publish**; полевой dry-run и homologation на реальном старте ещё не закрыты. UX-итерация начата (канон + Quick Wins), role modes Athlete/Judge/Control Room — первый срез в 0.5.11. Каталог выдачи приложения — в Event App, нативных APK/IPA **нет**.

Сверка с journeys: [ROLE_JOURNEYS_RECONCILIATION.md](./ROLE_JOURNEYS_RECONCILIATION.md).  
UX/UI канон: [UX_UI_CANON.md](../PRODUCT/UX_UI_CANON.md).  
Сверка с прикреплёнными DOCX: [GAP_VS_ATTACHED_DOCS.md](./GAP_VS_ATTACHED_DOCS.md) — **не всё из экосистемы/Hub относится к этому репо**.

## Staging (remote)

- Host: Timeweb VPS `62.113.42.227` (`mywave-bot-server`), каталог `/var/www/mywave-event-app` — отдельно от ботов.
- Стек: `docker compose -f docker-compose.staging.yml`, `APP_ENV=staging`.
- Выкат **0.5.13** (`ba2df6b` → `7795deb`), 2026-09-22. API Healthy, web Started. Production не трогали.
- Backup перед выкатом: `/var/backups/mywave-event-app/mywave_event_staging.20260921T142129Z.db` (614400 байт).
- Web login: http://62.113.42.227:3001/login — HTTP 200 (на сервере 2026-09-22).
- API health: `{"status":"ok","app":"MyWave Event App (Staging)","env":"staging","db_ok":true}` (2026-09-22T08:28:37Z).
- `GET /api/v1/auth/login-options`: `otp_required=false` (SMTP не настроен).
- Manifest: app.version **0.5.10**, documentation `available`; android / ios / source `unavailable`.
- Гость: события Казани по-прежнему `draft` на витрине. Казань не публиковать.
- SMTP нет — вход по известному телефону без OTP (роль из аккаунта). OTP снова включится, когда зададут SMTP.
- Это **не** production. Production не менялся.

## Работает

- Remote + CI + release + staging runbook.
- Auth / roles / consent / notifications / applications / roster / training slots.
- Documents, checklist, heats / start list / runs.
- Results draft → verified → **published только chief_judge** (0.5.9).
- Roster lock: фиксирует состав; check-in и судейство остаются.
- Rules catalog + EventRulesProfile (FVLS/IWWF).
- ProtocolCapture (фото/PDF); publish протокола — chief_judge.
- **FieldMoment (0.5.11, на staging с `ba2df6b`):** камера PWA для media/commentator/support/organizer+/chief_judge; не протокол, не витрина.
- Structured scoring, official protocol export, Athlete ID, archive lock.
- **UX 0.5.6–0.5.7:** публичная витрина, светлая тема, закрытые ролевые пути.
- **0.5.8:** AthleteProfile + Import Center + pending_claim. ADR-0007 **accepted**.
- Транскрипт бумажных протоколов Казани + места ФВЛС 15.08.2026 в **draft**. Не homologated → не публикуется автоматически. Площадка: оз. Нижний Кабан.
- **0.5.9:** ADR-0008 roster lock + chief_judge; journeys в `docs/PRODUCT/journeys/`.
- **Champ App UX/UI 1.0 (foundation):** `UX_UI_CANON.md`; Russian-only UI в AGENTS/PRD; Events (Идёт сейчас / Ближайшие / Мои / Архив); nearest event; mobile bottom nav без «Выйти»; notifications deep-link; live heat primary CTA + `•••`; «Следующий шаг» на карточке события; Field foundation; user-facing ошибки без «API/dev».
- **0.5.10:** карточка выдачи MyWave Event App в «Проекты → Чек-лист организатора» и на вкладке подготовки события. API `app-downloads` + analytics ingest. Android/iOS/source **не подключены**. Документация установки bundled. ADR-0009.
- **0.5.11 (git, на staging `ba2df6b`):** FieldMoment камера PWA; Athlete «Мой старт»; Organizer Control Room; Judge current athlete.
- **0.5.13 (на staging с `7795deb`, 2026-09-22):** вход по известному телефону без OTP и без пароля, пока SMTP не настроен; роль из аккаунта. Локально: `+79160117179` → «Админ платформы»; неизвестный номер отказан. Прогон судьи с другого телефона — pending. Production OTP не отключается.
- **0.5.14 (локально, до выката):** удаление из стартового списка (organizer+/chief_judge); мобильная навигация со всеми разделами; русские строки без тех. EN; скролл разделов чек-листа; empty states с подсказками.

## Частично / нет

- Полные role modes: Athlete Event Home / Organizer Control Room / Judge current — **первый срез на карточке события** (обзор + судейство); вкладки кабинета ещё есть. Broadcast — нет.
- Казань: нет баллов части финалов и части квалиф.; O40 только пьедестал WB boat men
- Commentator / photographer: FieldMoment-срез (камера) в коде; нет EXIF, Athlete ID match, личного альбома, публикации наружу
- ParserNews / volunteer / boat captain / полный broadcast rundown
- PDF protocol export
- SMTP — owner
- Telegram/MAX/native — не Stage 1 этого репо
- Native iOS/Android — нет (PWA)
- Полевой dry-run судья+организатор+chief на площадке — не выполнен
- PR #2 в `main` не влит (`main` = 0.5.7)
- В логе деплоя 0.5.9 сначала не было копии SQLite; backup сделан 2026-09-15T15:03Z (580K). Данные Казани не потеряны.

## Следующий P0

Порядок: [QA_AND_UX_HARDENING_PLAN.md](../PRODUCT/QA_AND_UX_HARDENING_PLAN.md). Native Android/iOS **после** волн 0–4.

1. Выкат **0.5.14** на staging (backup SQLite → pull → compose up → smoke).
2. Вход судьи с другого телефона (заявка → Доступы → вход без кода) — на staging или локально.
3. Полевой прогон трёх ролей на PWA (баги, 403 publish, roster lock, live heat, вкладка «Моменты», 11 разделов, мобильная навигация).
4. ~~Дописать backup SQLite на хост~~ — сделано перед 0.5.13.
5. UX: Athlete / Control Room / Judge / Моменты / справочник площадки — на staging; кабинеты-вкладки ещё есть.
6. Письмо сайту — точный текст в `docs/INTEGRATIONS/SITE_MYWAVE_DOWNLOAD_HANDOFF.md` (вариант A; Android/iOS недоступны).
7. SMTP на staging — владелец.
8. Карточка Казани `draft` → витрина только явным решением; результаты не публиковать.
9. Native-сборки и реальные `MYWAVE_EVENT_APP_*_URL` — только после чеклиста волн 0–4. **Не** подставлять example.org / xxxxxxxx.

## Проверки

- pytest: **115 passed** (phone login без OTP + FieldMoment + каталог выдачи + authz участника + upload + analytics PII)
- tsc: **passed** (включая справочник 11 разделов)
- lint (next lint): **passed**, без warning
- production build web: **passed** ранее на 0.5.10; tsc/lint зелёные после FieldMoment
- smoke staging **0.5.13** (2026-09-22): health `db_ok`; `login-options.otp_required=false`; `/login` 200; git `7795deb`; backup `mywave_event_staging.20260921T142129Z.db` (614400).
- npm audit (prod): 4 CVE в дереве `next` (в т.ч. RCE Image Optimization на Windows) — **не** закрыто слепым `audit fix`; TD-19

# CURRENT_STATE

Дата сверки: 2026-10-26

## Release review — 26 октября 2026

- PR #2 и #3 открыты, CI их текущих head зелёный; зарегистрированных GitHub reviews / review threads нет.
- Фактический application diff `581b924..c26a466` до review: один service экспорта Athlete ID, один regression test; web/Compose/модели не менялись.
- Новый blocker воспроизведён в отдельной SQLite: после `verified` и `published` судья мог изменить лист 75 → 100 (HTTP 201), а итог оставался 75. Текущий экспорт становился внутренне противоречивым.
- В `fix/finalized-judge-score-lock` подготовлен минимальный guard: `409 immutable` для листов проверенного/опубликованного результата; учитывается прежний heat при переносе. Возврат в draft / chief void использует прежние роли и history; миграций нет.
- Точечная локальная проверка: **15 passed** (11 новых scoring-сценариев + 4 проверки Athlete ID). Полная local/Docker/CI валидация фиксируется в PR этого изменения; до его интеграции staging-кандидат не считать завершённым. Полный review всего PR #2 (164 файла) этим целевым review не удостоверяется.
- Сервер и реальное соревнование не менялись. Web Dockerfile использует `npm install` без lockfile; для ближайшего минимального staging-кандидата планируется ограничить выкладку API, с отдельным доказательством его image identity и сохранением web/loopback bindings.

## SQLite backup/restore — 26 октября 2026, 11:38 UTC

- По live-выводу владельца `Invoke-BackupVerify.ps1` завершился **BACKUP_RESTORE_PASS**: online snapshot staging SQLite и восстановление в отдельном одноразовом контейнере прошли. Gate свежей **SQLite** копии и изолированного restore закрыт.
- Backup: `/var/backups/mywave-event-app/mywave_event_staging.20261026T113815Z.r3bwDHHf.db` (618496 байт); proof: тот же путь + `.verify.json`.
- SHA256 файла: `d4a2bab47043a8586ddf7893373dc90668c2500b06b6b4cb3147965c1eec63ba`.
- Snapshot и restore: **27 таблиц, 1324 строки**, `integrity_check=ok`, FK violations **0**, row counts и logical SHA256 совпадают: `68ff8fa32c1b8d9f2540df5c4aeb81f541aba530cc333a28759912b298ddb81e`.
- `source_mode=ro`, `restored_temp_removed=true`, `active_database_writes=false`, `application_restarts=false`. API/web container identities и hash dirty Compose сохранились; код приложения не разворачивался, рабочая БД не заменялась.
- Источник evidence — консольный live-вывод владельца за `2026-10-26T11:38:17.683420Z`; более ранние два SSH banner timeout агента не были успешным backup. Повторное резервирование этим checkpoint не выполнялось.
- `offsite_verified=false`; env/uploads и полное восстановление приложения этим SQLite-сценарием не удостоверяются. Остаются review/интеграция PR #2 → #3, сохранение loopback bindings, доказанная identity новых API/web images и отдельный полевой акт. Merge/deploy не выполнены.

## Staging checkpoint — 26 октября 2026, 05:49 UTC

- Повторный read-only SSH прошёл: API healthy, `env=staging`, OpenAPI **0.5.14**, `db_ok=true`; web `/login` **200**, BUILD_ID `p3AXeSOsU4Q12km3-554Z`.
- Серверный checkout: `581b92423422c59cea75a07255cccf8dd4859988`. Все **98 tracked файлов `services/api/app`** побайтово совпадают с `/app/app` работающего API; missing/different/extra — 0. Это подтверждает только файлы приложения, не происхождение всего image.
- API image: `sha256:6e59fc81e6281460e1da16390d4f95133f91822e77cc53de33e6a36de08d634e`; web image: `sha256:5c68d08ba5b25b1933b3f329a43c6c93c7216dc8f68b242b943606526064edb5`; оба созданы 2026-10-23. Revision labels пусты: **image build SHA / web source SHA неизвестны**.
- Единственный серверный diff `docker-compose.staging.yml`: `8001:8000` → `127.0.0.1:8001:8000` и `3001:3000` → `127.0.0.1:3001:3000`. Других изменённых строк нет. Сохранить эти ограничения при будущей интеграции; не сбрасывать dirty Compose.
- Runtime web: product **0.5.14**, Next.js **15.5.26**; локальная проверенная сборка использовала **15.5.22**. Не считать эти web-сборки одинаковыми. Внешний HTTP к IP:8001/3001 не является проверкой сервиса, опубликованного только на loopback.
- SQLite: 618496 байт, read-only `SELECT 1=1`, `quick_check=ok`. Последний показанный backup: `mywave_event_staging.20260923T045707Z.db`; свежий backup и restore proof не получены.
- `otp_required=false`, `password_required=false`: staging сохраняет вход по известному телефону без настроенной почтовой доставки. Конфигурация auth не менялась.
- Исправление Athlete ID — PR #3, code commit `0df9615`; в работающем API его ещё нет. PR #2 и #3 остаются открытыми. Следующий gate: review/порядок интеграции, свежий backup/restore, сохранение loopback bindings, доказанная identity новых API/web images и отдельный полевой акт.
- PowerShell → Bash: файл скрипта имел LF, но текстовый native pipeline добавлял завершающий CRLF. Передача через `tr -d "\015" | bash -s` проверена локально в Docker и на S1; exit 0. Сервер не перезапускался, fetch/checkout/миграции и записи в БД не выполнялись.

## Checkpoint release/staging — 25 октября 2026

- GitHub `main`: `ebb43b7c4fc75e5a5ea9778394182c58deb2bd73`.
- Кандидат PR #2: `cursor/p0-import-center-athlete-link`, `e2f602fd5c4da018ce2ce6d194817c7386e8d481`; PR открыт, 16 коммитов сверх main. CI run `35845927322` — success.
- Локальный baseline: API **116 passed**, Python dependencies `pip check` — passed; SQLite read-only `SELECT 1` / `quick_check` — passed. Web production build Next.js 15.5.22 — passed.
- Сквозной синтетический API dry-run воспроизвёл blocker: импортированные Athlete ID присутствуют в roster, но теряются в JSON official protocol (`null`); при наличии аккаунта экспорт мог подставить ID аккаунта вместо профиля спортсмена.
- Исправление в `fix/official-protocol-athlete-id`: экспорт использует профиль спортсмена с fallback для legacy User; без миграции, без изменения ролей или схемы ответа. Регресс-тесты до исправления: **2 failed / 2 passed**.
- Полный локальный API suite после исправления: **120 passed**, 0 skipped (116 существующих + 4 проверки идентичности). Web не менялся; baseline production build остаётся passed. Автоматический API dry-run и полевой акт учитываются отдельно.
- Актуальный staging: **deployed_sha=null**, версия и состояние БД неизвестны. SSH `22`, API `8001` и web `3001` с этой машины дали timeout. Это не доказательство остановки сервиса.
- Данные ниже — историческое свидетельство за сентябрь. До выкладки нужны текущие identity API/web, проверенный backup/restore, review/CI и отдельный полевой акт организатора и главного судьи. Production, staging и данные Казани этим циклом не изменялись.

## Исторический срез — 23 сентября 2026

Версия продукта: **0.5.14 на staging** (git `581b924`) — вход по телефону без OTP, пока SMTP не настроен. Каталог выдачи в manifest по-прежнему подписан **0.5.10** (документация; android/ios недоступны).  
Путь до DoD v1 (аудит): ~**86%** — identity + import + транскрипт Казани + **roster lock / chief-judge publish**; полевой dry-run и homologation на реальном старте ещё не закрыты. UX-итерация начата (канон + Quick Wins), role modes Athlete/Judge/Control Room — первый срез в 0.5.11. Каталог выдачи приложения — в Event App, нативных APK/IPA **нет**.

Сверка с journeys: [ROLE_JOURNEYS_RECONCILIATION.md](./ROLE_JOURNEYS_RECONCILIATION.md).  
UX/UI канон: [UX_UI_CANON.md](../PRODUCT/UX_UI_CANON.md).  
Сверка с прикреплёнными DOCX: [GAP_VS_ATTACHED_DOCS.md](./GAP_VS_ATTACHED_DOCS.md) — **не всё из экосистемы/Hub относится к этому репо**.

## Staging (remote)

- Host: Timeweb VPS `62.113.42.227` (`mywave-bot-server`), каталог `/var/www/mywave-event-app` — отдельно от ботов.
- Стек: `docker compose -f docker-compose.staging.yml`, `APP_ENV=staging`.
- Выкат **0.5.14** (`7795deb` → `581b924`), 2026-09-22T18:18Z. API Healthy, web Started. Production не трогали.
- Backup перед выкатом 0.5.14: **не записался** (опечатка `er cp`). Post-deploy backup: `/var/backups/mywave-event-app/mywave_event_staging.20260923T045707Z.db` (618496 байт, 2026-09-23). Ранее: `…20260921T142129Z.db` (614400).
- Web login: http://62.113.42.227:3001/login — HTTP 200 (снаружи 2026-09-23).
- API health: `{"status":"ok","app":"MyWave Event App (Staging)","env":"staging","db_ok":true}` (2026-09-23T04:27Z).
- OpenAPI version: **0.5.14**.
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
- **0.5.14 (на staging с `581b924`, 2026-09-22):** удаление из стартового списка (organizer+/chief_judge); мобильная навигация со всеми разделами; русские строки без тех. EN; скролл разделов чек-листа; empty states с подсказками. Pre-deploy backup 0.5.14 не записался — нужен post-deploy backup.

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

1. ~~Выкат **0.5.14** на staging~~ — сделано 2026-09-22, SHA `581b924`, OpenAPI `0.5.14`, `otp_required=false`, web login 200. Pre-deploy backup не записался (`er cp`).
2. ~~Post-deploy backup SQLite~~ — `mywave_event_staging.20260923T045707Z.db` (618496), 2026-09-23.
3. Вход судьи с другого телефона (заявка → Доступы → вход без кода) — на staging или локально.
4. Полевой прогон трёх ролей на PWA (баги, 403 publish, roster lock, live heat, вкладка «Моменты», 11 разделов, мобильная навигация).
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
- smoke staging **0.5.14** (2026-09-22/23): health `db_ok`; OpenAPI `0.5.14`; `login-options.otp_required=false`; `/login` 200; git `581b924`; post-deploy backup `mywave_event_staging.20260923T045707Z.db` (618496).
- npm audit (prod): 4 CVE в дереве `next` (в т.ч. RCE Image Optimization на Windows) — **не** закрыто слепым `audit fix`; TD-19

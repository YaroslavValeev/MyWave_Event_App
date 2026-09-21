# CURRENT_STATE

Дата: 2026-09-21  
Версия продукта: **0.5.13 локально** (вход по телефону без OTP); staging ещё **0.5.11/0.5.12** (`ba2df6b`), пока этот SHA не выкатят. Каталог выдачи в manifest по-прежнему подписан **0.5.10** (документация; android/ios недоступны).  
Путь до DoD v1 (аудит): ~**86%** — identity + import + транскрипт Казани + **roster lock / chief-judge publish**; полевой dry-run и homologation на реальном старте ещё не закрыты. UX-итерация начата (канон + Quick Wins), role modes Athlete/Judge/Control Room — первый срез в 0.5.11. Каталог выдачи приложения — в Event App, нативных APK/IPA **нет**.

Сверка с journeys: [ROLE_JOURNEYS_RECONCILIATION.md](./ROLE_JOURNEYS_RECONCILIATION.md).  
UX/UI канон: [UX_UI_CANON.md](../PRODUCT/UX_UI_CANON.md).  
Сверка с прикреплёнными DOCX: [GAP_VS_ATTACHED_DOCS.md](./GAP_VS_ATTACHED_DOCS.md) — **не всё из экосистемы/Hub относится к этому репо**.

## Staging (remote)

- Host: Timeweb VPS `62.113.42.227` (`mywave-bot-server`), каталог `/var/www/mywave-event-app` — отдельно от ботов.
- Стек: `docker compose -f docker-compose.staging.yml`, `APP_ENV=staging`.
- Выкат **0.5.11+** (`6ce503b` → `ba2df6b`), 2026-09-19T05:08Z. API Healthy, web Started. Production не трогали.
- Backup на хост **перед** этим выкатом не записался (сменилась сессия/`$STAMP`, `docker cp` не нашёл файл). Volume SQLite, судя по `db_ok`, сохранился. Предыдущий хостовый backup: `...20260917T100554Z.db` (580K). Нужна копия **сейчас** с живого контейнера.
- Web: http://62.113.42.227:3001/projects/checklist-org — HTTP 200 (проверка снаружи 2026-09-19).
- API health (на сервере): `{"status":"ok","app":"MyWave Event App (Staging)","env":"staging","db_ok":true}` (2026-09-19T05:08:23Z). С ноутбука `/health` иногда таймаутит.
- OpenAPI: `"version":"0.5.11"`.
- Manifest: app.version **0.5.10**, `available_count: 1` — documentation `available`; android / ios / source `unavailable` (URL сборок **не** прописаны — так и должно быть).
- Гость: события Казани по-прежнему `draft` на витрине. Казань не публиковать.
- SMTP нет — в коде 0.5.13 вход по известному телефону без OTP (роль из аккаунта). На staging это появится после выката 0.5.13. OTP снова включится, когда зададут SMTP.
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
- **0.5.13 (локально 2026-09-21, на staging ещё нет):** вход по известному телефону без OTP и без пароля, пока SMTP не настроен; роль из аккаунта. Живая проверка: `+79160117179` → «Админ платформы»; неизвестный номер отказан; карточка Казани открылась. Прогон судьи с другого телефона — вечером. Production OTP не отключается.

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

1. ~~Выкат **0.5.11+** на staging~~ — сделано 2026-09-19, SHA `ba2df6b`. **Дописать backup SQLite на хост** перед выкатом 0.5.13 (см. STAGING.md).
2. Выкат **0.5.13** на staging (phone login без OTP). Production не трогать. Казань не публиковать.
3. Вечером: вход судьи с другого телефона (заявка → Доступы → вход без кода).
4. Полевой прогон трёх ролей на PWA (баги, 403 publish, roster lock, live heat, вкладка «Моменты», 11 разделов).
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
- smoke staging **0.5.11** (2026-09-19T05:08Z): health `db_ok`; OpenAPI 0.5.11; manifest documentation available, android/ios/source unavailable; `/projects/checklist-org` 200 снаружи; git `ba2df6b`. Хостовый backup этого выката — **ещё нет**.
- npm audit (prod): 4 CVE в дереве `next` (в т.ч. RCE Image Optimization на Windows) — **не** закрыто слепым `audit fix`; TD-19

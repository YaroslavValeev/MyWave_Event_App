# CURRENT_STATE

Дата: 2026-11-04
Версия продукта: **0.5.18** (PDF/DOCX + Playwright API SC01–09 PASS; Android APK BLOCKED)
Путь до DoD v1 (аудит): ~**80%** — остаток почти целиком **пилот на площадке**, не «дыры» ядра Stage 1.
План дожима: [NEXT_HARDENING_PLAN.md](../OPERATIONS/NEXT_HARDENING_PLAN.md).
Программа Champ modernization: [CHAMP_MODERNIZATION_PROGRAM.md](./CHAMP_MODERNIZATION_PROGRAM.md).

Сверка с прикреплёнными DOCX: [GAP_VS_ATTACHED_DOCS.md](./GAP_VS_ATTACHED_DOCS.md) — **не всё из экосистемы/Hub относится к этому репо**.

## Работает

- Remote + CI + release + staging runbook.
- Auth / roles / consent / notifications / applications / roster / training slots.
- Documents, checklist, heats / start list / runs.
- Results draft → verified → published → void.
- Rules catalog + EventRulesProfile (FVLS/IWWF).
- ProtocolCapture (фото/PDF).
- Structured scoring, official protocol export (JSON + HTML), Athlete ID, archive lock.
- **UX 0.5.6:** публичная витрина событий (J4); ролевые вкладки; русские статусы; вход без dev-console; регистрация участником по умолчанию; нижняя навигация на телефоне.
- **UX 0.5.7:** светлая тема, бирюзовые обводки и тени кнопок. Просроченный токен не тупик: гостевой просмотр + «Войти снова» с возвратом. Ролевые пути закрыты CTA. GET heats публичный на витрине (start list по-прежнему с входом).
- **Отчётность 0.5.8–0.5.13:** Dual-track; AI assemble (local / OpenAI-compatible / Ollama); Excel; role handoffs. VPS РФ: `api.openai.com` → 403 territory; staging использует Ollama.
- **Staging ops 0.5.14:** `DATA_DIR=/data`, `/health.version`, `scripts/staging_up.sh`, compose ollama override, nginx example, SMTP/tunnel runbooks.
- **Roster 0.5.15:** `name_latin` + оба написания на карточке; скрипт слияния RU/EN-дублей.
- **Publications 0.5.16:** лента post/news, серверный RBAC, media JPG/PNG/WebP, Idempotency-Key, UI вкладка «Лента», локальные offline-черновики (не полный offline MVP).
- **Guidance / Scoreboard / Protocol revisions 0.5.17:** ролевые подсказки; табло + SSE; immutable protocol revisions; workflow Mermaid A–I.
- **Protocol PDF/DOCX 0.5.18:** native export (reportlab/python-docx) для live и утверждённых ревизий.
- **E2E 0.5.18:** Playwright `e2e/` — API SC01–SC09 **PASS** (2026-11-04, local API :8020); SC10 Xiaomi — manual/NOT RUN; UI smoke — при поднятом web.

## Частично / нет

- Live board polish / DNS-DNF UX (базовый scoreboard 0.5.17 есть; polish остаётся)
- Offline scoring queue с конфликтами версий JudgeScore — нет (только черновики публикаций)
- Field moments / STT — flags off; ParserNews только published report
- Media / Photographer Mode Stage 5 (EXIF ↔ heat) — ещё нет; лента публикаций — первый слой
- Broadcast Stage 8 — нет
- Offline sync Stage 3 (IndexedDB queue auto-flush) — нет; только localStorage drafts ленты
- Score-now / Excel import adapters (seed Excel есть; live-import — нет)
- ~~PDF protocol export~~ — PDF/DOCX есть (0.5.18); юридическая «официальность» только через revision
- **SMTP на staging** — код готов, ключи/пароль — **owner**
- **Публичный HTTPS URL** — пример nginx есть; DNS/certs — **owner**
- Диск VPS / prune — **owner**
- Telegram/MAX — не Stage 1 этого репо
- Native iOS/Android APK — **нет** (PWA / ADR-0014)
- Полевой dry-run судья+организатор на площадке — **не выполнен** (главный блокер DoD v1)
- Проверка на Xiaomi 14 — **не выполнена** (чек-лист готов)

## Следующий P0

| # | Что | Кто | Зачем |
|---|-----|-----|-------|
| 1 | Pilot dry-run одного события (судья + организатор) | owner + 1–2 роли | закрыть DoD v1 |
| 2 | SMTP + публичный staging (nginx/домен) | owner | OTP на почту + доступ без туннеля |
| 3 | ~~Deep-link / UI Отчёт / Ollama AI~~ | **done 0.5.9–0.5.14** | — |
| 4 | ~~PDF protocol export~~ | **done 0.5.18** | JSON/HTML live + PDF/DOCX |
| 5 | Media / photographer mode | код Stage 5 | после стабильного дня старта |
| 6 | JDK/SDK → debug APK + Xiaomi X14-* | owner tooling + device | APK сейчас BLOCKED |

Виртуальный прогон: [KAZAN_VIRTUAL_DRY_RUN.md](../PRODUCT/KAZAN_VIRTUAL_DRY_RUN.md). Модель отчёта: [EVENT_REPORTING_MODEL.md](../PRODUCT/EVENT_REPORTING_MODEL.md).

## Проверки

- pytest 0.5.7: public events + invalid bearer as guest + guest heats
- pytest 0.5.9: `test_event_report.py` — AI assemble / excel / role-actions / flags / authz
- pytest 0.5.18: `test_protocol_documents.py` — PDF/DOCX live + revision (2 passed)
- Playwright 0.5.18: API SC01–SC09 passed; SC10 skipped (device manual)
- Android: `apps/mobile` Capacitor scaffold; doctor — Java/ANDROID_HOME **MISSING** → APK **BLOCKED**
- Xiaomi 14: чек-лист X14-01…20 готов; device **NOT RUN**
- UI: светлый фон; бирюза на кнопках; истекшая сессия → «Войти снова»

## Факт репозитория на 2026-11-04

- Не заявлять: mobile APK/IPA, prod deploy, полный offline MVP, Xiaomi PASS — этого нет.
- Publications 0.5.16 + guidance/scoreboard/revisions 0.5.17 + PDF/DOCX/E2E 0.5.18 в коде.
- `data/downloads/` — служебные; в git не коммитить без необходимости.

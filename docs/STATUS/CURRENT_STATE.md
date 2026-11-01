# CURRENT_STATE

Дата: 2026-11-01  
Версия продукта: **0.5.14** (staging harden: DATA_DIR, health.version, ollama compose override, runbooks)  
Путь до DoD v1 (аудит): ~**80%** — остаток почти целиком **пилот на площадке**, не «дыры» ядра Stage 1.  
План дожима: [NEXT_HARDENING_PLAN.md](../OPERATIONS/NEXT_HARDENING_PLAN.md).

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

## Частично / нет

- Live board / polish DNS-DNF UX (базовые лейблы есть)
- Field moments / STT — flags off; ParserNews только published report
- Media / broadcast — этапы 5–8
- Score-now / Excel import adapters (seed Excel есть; live-import — нет)
- PDF protocol export (HTML → Print пока достаточно)
- **SMTP на staging** — код готов, ключи/пароль — **owner**
- **Публичный HTTPS URL** — пример nginx есть; DNS/certs — **owner**
- Диск VPS / prune — **owner**
- Telegram/MAX/native — не Stage 1 этого репо
- Native iOS/Android — нет (PWA)
- Полевой dry-run судья+организатор на площадке — **не выполнен** (главный блокер DoD v1)

## Следующий P0

| # | Что | Кто | Зачем |
|---|-----|-----|-------|
| 1 | Pilot dry-run одного события (судья + организатор) | owner + 1–2 роли | закрыть DoD v1 |
| 2 | SMTP + публичный staging (nginx/домен) | owner | OTP на почту + доступ без туннеля |
| 3 | ~~Deep-link / UI Отчёт / Ollama AI~~ | **done 0.5.9–0.5.14** | — |
| 4 | PDF protocol export | код (optional) | если Print HTML мало |
| 5 | Media / photographer mode | код Stage 5 | после стабильного дня старта |

Виртуальный прогон: [KAZAN_VIRTUAL_DRY_RUN.md](../PRODUCT/KAZAN_VIRTUAL_DRY_RUN.md). Модель отчёта: [EVENT_REPORTING_MODEL.md](../PRODUCT/EVENT_REPORTING_MODEL.md).

## Проверки

- pytest 0.5.7: public events + invalid bearer as guest + guest heats
- pytest 0.5.9: `test_event_report.py` — AI assemble / excel / role-actions / flags / authz
- UI: светлый фон; бирюза на кнопках; истекшая сессия → «Войти снова»

## Факт репозитория на 2026-10-27

- Последний продуктовый merge: PR #1 `ux-0.5.7-light-theme-journeys`.
- Незакоммичено локально: `data/downloads/` (служебные файлы; в git не коммитить без необходимости).
- Не заявлять: mobile APK/IPA, prod deploy, offline MVP — этого нет.

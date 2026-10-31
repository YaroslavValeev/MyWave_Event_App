# CURRENT_STATE

Дата: 2026-10-27  
Версия продукта: **0.5.10** (deep-link уведомлений + dry-run Казань + auto-port; отчётность с 0.5.9)  
Путь до DoD v1 (аудит): ~**80%** — остаток почти целиком **пилот на площадке**, не «дыры» ядра Stage 1.

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
- **Отчётность 0.5.8–0.5.9:** Dual-track; виртуальный прогон Казани; AI assemble (local/OpenAI); Excel export; матрица физ. действий ↔ ролей.

## Частично / нет

- Live board / polish DNS-DNF UX (базовые лейблы есть)
- Field moments / STT / LLM-draft отчёта — flags off; ParserNews читает только published report (этап 7)
- Media / broadcast — этапы 5–8
- Score-now / Excel import adapters (seed Excel есть; live-import — нет)
- PDF protocol export (HTML → Print пока достаточно)
- SMTP + remote staging host — **owner**
- Telegram/MAX/native — не Stage 1 этого репо
- Native iOS/Android — нет (PWA)
- Полевой dry-run судья+организатор на площадке — **не выполнен** (главный блокер DoD v1)

## Следующий P0

| # | Что | Кто | Зачем |
|---|-----|-----|-------|
| 1 | Pilot dry-run одного события (судья + организатор) | owner + 1–2 роли | закрыть DoD v1 |
| 2 | Production SMTP + доступный staging host | owner | реальные OTP/approve письма |
| 3 | ~~Deep-link уведомлений~~ | **done 0.5.10** | href в API + UI «Открыть» |
| 4 | PDF protocol export | код (optional) | если Print HTML мало |
| 5 | ~~UI вкладка «Отчёт»~~ | **done 0.5.9** | Excel + AI + handoffs в UI |
| 6 | Media / photographer mode | код Stage 5 | только после стабильного дня старта |

Виртуальный прогон: [KAZAN_VIRTUAL_DRY_RUN.md](../PRODUCT/KAZAN_VIRTUAL_DRY_RUN.md). Модель отчёта: [EVENT_REPORTING_MODEL.md](../PRODUCT/EVENT_REPORTING_MODEL.md).

## Проверки

- pytest 0.5.7: public events + invalid bearer as guest + guest heats
- pytest 0.5.9: `test_event_report.py` — AI assemble / excel / role-actions / flags / authz
- UI: светлый фон; бирюза на кнопках; истекшая сессия → «Войти снова»

## Факт репозитория на 2026-10-27

- Последний продуктовый merge: PR #1 `ux-0.5.7-light-theme-journeys`.
- Незакоммичено локально: `data/downloads/` (служебные файлы; в git не коммитить без необходимости).
- Не заявлять: mobile APK/IPA, prod deploy, offline MVP — этого нет.

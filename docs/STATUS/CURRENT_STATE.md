# CURRENT_STATE

Дата: 2026-08-31  
Версия продукта: **0.5.8** (ветка `cursor/p0-import-center-athlete-link`; tag после merge)  
Путь до DoD v1 (аудит): ~**84%** — identity + import + транскрипт сканов Казани в черновики; live scoring / homologation / publish на реальном старте ещё не закрыты.

Сверка с прикреплёнными DOCX: [GAP_VS_ATTACHED_DOCS.md](./GAP_VS_ATTACHED_DOCS.md) — **не всё из экосистемы/Hub относится к этому репо**.

## Staging (remote)

- Host: Timeweb VPS `62.113.42.227` (`mywave-bot-server`), каталог `/var/www/mywave-event-app` — отдельно от ботов.
- Стек: `docker compose -f docker-compose.staging.yml`, `APP_ENV=staging`.
- Web: http://62.113.42.227:3001 — HTTP 200.
- API health: `{"status":"ok","app":"MyWave Event App (Staging)","env":"staging","db_ok":true}` (2026-08-30T04:10:27Z).
- На сервере до обновления 0.5.8: **v0.5.7** / SHA `ebb43b7`, пустая SQLite, без seed Казани. SMTP нет — OTP в mail_outbox.
- Это **не** production. Production не менялся.

## Работает

- Remote + CI + release + staging runbook.
- Auth / roles / consent / notifications / applications / roster / training slots.
- Documents, checklist, heats / start list / runs.
- Results draft → verified → published → void.
- Rules catalog + EventRulesProfile (FVLS/IWWF).
- ProtocolCapture (фото/PDF).
- Structured scoring, official protocol export, Athlete ID, archive lock.
- **UX 0.5.6–0.5.7:** публичная витрина, светлая тема, закрытые ролевые пути.
- **0.5.8:** AthleteProfile + Import Center + pending_claim. ADR-0007 **accepted** (IWWF U14/U18/O30/O40/Open, одно событие ЧР+ПР).
- Расписание на обзоре события коррелирует с карточкой (город/даты/слоты); хардкод Казани снят.
- Транскрипт бумажных протоколов Казани + итоговые места из поста ФВЛС 15.08.2026 раскладываются в заезды / start list / **draft** results. Мастерс → O30 (O40 в посте не разделён). Не homologated → не публикуется автоматически. Площадка: оз. Нижний Кабан.

## Частично / нет

- Казань-2026 в staging: roster после deploy + Import Center; сканы + пост ФВЛС — после `scan-protocol` / кнопки в `/admin/imports`
- Нет баллов финалов (только места ФВЛС); нет баллов: Junior Men WB qual, Open Men WB/WS qual, U14/U18 skim qual
- O40 ветераны вейкборд-катер (муж.): пьедестал Чернов / Матвеев / Дементьев — черновик, без баллов финала
- Commentator / photographer / EXIF / ParserNews
- PDF protocol export
- SMTP — owner
- Telegram/MAX/native — не Stage 1 этого репо
- Native iOS/Android — нет (PWA)
- Полевой dry-run судья+организатор на площадке — не выполнен

## Следующий P0 (после деплоя import)

1. Deploy + `scan-protocol` на событии «Чемпионат России в Казани 2026»
2. Баллы финалов, если появятся IWWF-листы; сплит Мастерс O30/O40 по возрасту
3. SMTP на staging

## Проверки

- pytest: import center + pending_claim + ingest-pack IWWF + scan-protocol (см. VALIDATION_REPORT)
- UI Import Center / claim — после staging deploy, browser smoke владельцем


# CURRENT_STATE

Дата: 2026-08-26  
Версия продукта: **0.5.4**  
Путь до DoD v1 (аудит): ~**62%**

Сверка с прикреплёнными DOCX: [GAP_VS_ATTACHED_DOCS.md](./GAP_VS_ATTACHED_DOCS.md) — **не всё из экосистемы/Hub относится к этому репо**.

## Работает

- Remote + CI + release + staging runbook.
- Auth / roles / consent / notifications / applications / roster / training slots.
- Documents, checklist, heats / start list / runs.
- Results draft → verified → published → void.
- Rules catalog + EventRulesProfile (FVLS/IWWF).
- ProtocolCapture (фото/PDF).
- **Structured scoring (0.5.3):** engines WSWS_DRIVE / IWWF_CABLE_TI / IWWF_BOAT_EIC; judge sheets; panel aggregate → result draft.
- **Official protocol export (0.5.4):** JSON bundle + HTML print + readiness.
- UI: wizard события, Протокол, **Судейство**, экспорт протокола.

## Частично / нет

- Athlete ID / media / archive / ParserNews / broadcast
- Score-now / Excel import adapters
- SMTP + remote staging host — owner
- Telegram/MAX/native — не Stage 1 этого репо

## Следующий P0 (код)

1. Athlete ID
2. Read-only archive after `completed`
3. PDF export (optional, from HTML)

## Проверки

- pytest: scoring + protocol + competition day
- UI: вкладка «Судейство» при scoring_mode=structured и engine ≠ MANUAL_PLACE

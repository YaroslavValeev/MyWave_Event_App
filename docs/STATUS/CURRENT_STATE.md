# CURRENT_STATE

Дата: 2026-08-25  
Версия продукта: **0.5.3**  
Путь до DoD v1 (аудит): ~**58%**

Сверка с прикреплёнными DOCX: [GAP_VS_ATTACHED_DOCS.md](./GAP_VS_ATTACHED_DOCS.md) — **не всё из экосистемы/Hub относится к этому репо**.

## Работает

- Remote + CI + release + staging runbook.
- Auth / roles / consent / notifications / applications / roster / training slots.
- Documents, checklist, heats / start list / runs.
- Results draft → verified → published → void.
- Rules catalog + EventRulesProfile (FVLS/IWWF).
- ProtocolCapture (фото/PDF).
- **Structured scoring (0.5.3):** engines WSWS_DRIVE / IWWF_CABLE_TI / IWWF_BOAT_EIC; judge sheets; panel aggregate → result draft.
- UI: wizard события, Протокол, **Судейство**.

## Частично / нет

- Official protocol PDF/JSON export
- Athlete ID / media / archive / ParserNews / broadcast
- Score-now / Excel import adapters
- SMTP + remote staging host — owner
- Telegram/MAX/native — не Stage 1 этого репо

## Следующий P0 (код)

1. Official protocol export
2. Athlete ID
3. Archive after completed

## Проверки

- pytest: scoring + protocol + competition day
- UI: вкладка «Судейство» при scoring_mode=structured и engine ≠ MANUAL_PLACE

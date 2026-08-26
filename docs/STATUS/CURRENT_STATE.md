# CURRENT_STATE

Дата: 2026-08-26  
Версия продукта: **0.5.5**  
Путь до DoD v1 (аудит): ~**70%**

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
- **Athlete ID (0.5.5):** opaque `MW-XXXXXXXX` на User; в roster/profile/protocol.
- **Archive lock (0.5.5):** `completed`/`cancelled` → read-only; reopen via status/`Вернуть в live`.
- UI: wizard, Протокол, Судейство, экспорт, баннер архива, DNS/DNF labels.

## Частично / нет

- Media / ParserNews / broadcast
- Score-now / Excel import adapters
- PDF export (HTML → Print пока достаточно)
- SMTP + remote staging host — owner
- Telegram/MAX/native — не Stage 1 этого репо

## Следующий P0 (код)

1. Live board / UX polish дня старта (дальше)
2. PDF protocol export (optional)
3. Pilot dry-run одного события

## Проверки

- pytest: athlete + archive + scoring + protocol
- UI: Athlete ID в профиле; архив блокирует правки; export на completed доступен

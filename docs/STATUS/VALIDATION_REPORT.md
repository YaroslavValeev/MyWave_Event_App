# Validation Report — MyWave Event App Stage 1 consent

Дата: 2026-08-24  
Продукт: standalone MyWave Event App  
Цикл: documents/consent minimal (ADR-0004)

## Проверки

| Проверка | Результат |
|---|---|
| API unit/integration (pytest) | **29 passed** |
| API pip install (ASCII venv `C:\tmp\mw_event_api_venv`) | passed (использован существующий venv) |
| Web `npm run build` | **passed** (Next.js 15.5.22) |
| lint frontend | included in `next build` (passed) |
| mobile build | N/A (Этап 3) |
| Docker build | not run on this workstation |
| Browser a11y axe | unavailable |
| Production deploy | not performed |

## Что подтверждено тестами

- `/health`, `/ready`, phone register/OTP, role approve
- event create/update permissions
- self-serve applications accept/reject
- legal catalog public
- register без обязательных согласий → `consent_required`
- grant/revoke опциональных; revoke обязательных → `consent_locked`
- roster маскирует self-serve ФИО без publish-consent; organizer видит ФИО; после grant маска снимается
- audit consent.granted / consent.revoked (через register/profile API)

## Ограничения

- Web build зависит от сети/npm; результат фиксируется командой `npm run build` в `apps/web`.
- SMTP/staging — блокеры владельца.
- Тексты LEGAL — рабочие редакции.
- Download Center остаётся архивом в `releases/`.

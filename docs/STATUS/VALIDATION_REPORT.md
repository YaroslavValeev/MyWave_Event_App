# Validation Report — MyWave Event App Stage 1

Дата: 2026-08-24  
Продукт: standalone MyWave Event App  
Цикл: email confirm POST (ADR-0005) + in-app notifications

## Проверки

| Проверка | Результат |
|---|---|
| API unit/integration (pytest) | **36 passed** |
| API pip install (Python 3.11) | passed |
| Web `npm run build` | **passed** (Next.js 15.5.22, маршрут `/notifications`) |
| lint frontend | included in `next build` (passed) |
| mobile build | N/A (Этап 3) |
| Docker build | not run on this workstation |
| Browser a11y axe | unavailable |
| Production deploy | not performed |

## Что подтверждено тестами

- `/health`, `/ready`, phone register/OTP, role approve (GET без мутации, POST confirm)
- pending list без token; OTP 6-й запрос → 429; production SECRET_KEY
- in-app notifications: заявка/роль, mark read
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

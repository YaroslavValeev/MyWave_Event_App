# API Contract (Stage 1 + auth/competition)

Базовый URL: `/`

## Health

| Method | Path | Auth | Описание |
|--------|------|------|----------|
| GET | `/health` | no | liveness + db_ok |
| GET | `/ready` | no | readiness (503 если DB down) |
| GET | `/api/v1/roles` | no | список ролей |

## Auth

| Method | Path | Auth | Описание |
|--------|------|------|----------|
| POST | `/api/v1/auth/register` | no | регистрация (participant active; иначе pending) |
| POST | `/api/v1/auth/phone/request-otp` | no | OTP на email + mail_outbox |
| POST | `/api/v1/auth/phone/verify-otp` | no | JWT при status=active |
| GET | `/api/v1/auth/approvals/pending` | Bearer organizer+ | очередь ролей |
| POST | `/api/v1/auth/approvals/{token}/approve` | Bearer organizer+ | утвердить |
| POST | `/api/v1/auth/approvals/{token}/reject` | Bearer organizer+ | отклонить |
| GET | `/api/v1/auth/approvals/{token}/approve` | no (email link) | HTML approve |
| GET | `/api/v1/auth/approvals/{token}/reject` | no (email link) | HTML reject |
| POST | `/api/v1/auth/dev-login` | no (dev/test only) | JWT bootstrap |
| GET | `/api/v1/me` | Bearer | текущий пользователь |
| PATCH | `/api/v1/me` | Bearer | имя и/или телефон |
| GET | `/api/v1/legal/documents` | no | каталог согласий/документов |
| GET | `/api/v1/legal/documents/{purpose}` | no | текст текущей версии |
| GET | `/api/v1/me/consents` | Bearer | согласия текущего пользователя |
| POST | `/api/v1/me/consents` | Bearer | выдать согласие (`purpose`, опционально `version`) |
| POST | `/api/v1/me/consents/{purpose}/revoke` | Bearer | отозвать опциональное согласие |

Регистрация (`POST /api/v1/auth/register`) требует `accept_terms` и `accept_privacy` = true (версии из каталога `2026-08-24`). Коды: `consent_required`, `consent_locked`, `unknown_purpose`.

## Events

| Method | Path | Auth | Описание |
|--------|------|------|----------|
| GET | `/api/v1/events` | Bearer | список |
| POST | `/api/v1/events` | Bearer organizer+ | создать |
| GET | `/api/v1/events/{id}` | Bearer | получить |
| PATCH | `/api/v1/events/{id}` | Bearer organizer+ | обновить |
| GET | `/api/v1/events/{id}/detail` | Bearer | сводка + counts |

## Competition

| Method | Path | Auth | Описание |
|--------|------|------|----------|
| GET | `/api/v1/events/{id}/categories` | Bearer | категории |
| GET | `/api/v1/events/{id}/participants` | Bearer | участники (**accepted/registered**, без phone; self-serve без publish-consent — псевдоним) |
| POST | `/api/v1/events/{id}/applications` | Bearer | подать заявку (registration_open) |
| GET | `/api/v1/events/{id}/applications/me` | Bearer | своя заявка |
| GET | `/api/v1/events/{id}/applications` | Bearer organizer+ | очередь заявок |
| PATCH | `/api/v1/events/{id}/applications/{participant_id}` | Bearer organizer+ | accept/reject |
| GET | `/api/v1/events/{id}/documents` | Bearer | документы |
| GET | `/api/v1/events/{id}/documents/{doc_id}/file` | Bearer | скачать файл |
| GET | `/api/v1/events/{id}/officials` | Bearer | судьи |
| GET | `/api/v1/events/{id}/training-slots` | Bearer | слоты (`only_booked`, `discipline`) |
| GET | `/api/v1/events/{id}/schedule-hint` | Bearer | текстовая подсказка расписания |
| GET | `/api/v1/audit` | Bearer admin | audit |

Ошибка:

```json
{ "error": { "code": "forbidden", "message": "..." } }
```

Подробности auth: `docs/OPERATIONS/AUTH_PHONE.md`  
Команды владельца: `docs/OPERATIONS/OWNER_COMMANDS.md`

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
| GET | `/api/v1/auth/approvals/pending` | Bearer organizer+ | очередь ролей (**без** token) |
| POST | `/api/v1/auth/approvals/{approval_id}/approve` | Bearer organizer+ | утвердить по id |
| POST | `/api/v1/auth/approvals/{approval_id}/reject` | Bearer organizer+ | отклонить по id |
| GET | `/api/v1/auth/approvals/{token}/approve` | no (email link) | HTML-форма подтверждения (без мутации) |
| GET | `/api/v1/auth/approvals/{token}/reject` | no (email link) | HTML-форма подтверждения (без мутации) |
| POST | `/api/v1/auth/approvals/{token}/confirm` | form `decision=approve\|reject` | мутация по email-ссылке |
| POST | `/api/v1/auth/dev-login` | no (dev/test only) | JWT bootstrap |
| GET | `/api/v1/me` | Bearer | текущий пользователь |
| PATCH | `/api/v1/me` | Bearer | имя и/или телефон |
| GET | `/api/v1/me/notifications` | Bearer | журнал уведомлений |
| GET | `/api/v1/me/notifications/unread-count` | Bearer | число непрочитанных |
| POST | `/api/v1/me/notifications/read-all` | Bearer | отметить все прочитанными |
| POST | `/api/v1/me/notifications/{id}/read` | Bearer | отметить одно |
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
| POST | `/api/v1/events` | Bearer organizer+ | создать (optional `rules_profile`: governing_body, sanction_body, discipline_codes[], scoring_mode) |
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
| POST | `/api/v1/events/{id}/documents` | Bearer organizer+ | upload (multipart: file, title, kind, language?, description?) |
| DELETE | `/api/v1/events/{id}/documents/{doc_id}` | Bearer organizer+ | удалить документ + файл |
| GET | `/api/v1/events/{id}/documents/{doc_id}/file` | Bearer | скачать файл |
| GET | `/api/v1/events/{id}/checklist` | Bearer | чеклист подготовки (auto-seed + auto-tick) |
| PATCH | `/api/v1/events/{id}/checklist/{item_id}` | Bearer organizer+ | `{"is_done": true\|false}` |
| GET | `/api/v1/events/{id}/heats` | Bearer | heats (≠ training slots) |
| POST | `/api/v1/events/{id}/heats` | Bearer organizer+ | создать heat |
| PATCH | `/api/v1/events/{id}/heats/{heat_id}/status` | Bearer organizer+ | planned\|ready\|on_water\|completed\|cancelled |
| GET | `/api/v1/events/{id}/heats/{heat_id}/start-list` | Bearer | start list |
| POST | `/api/v1/events/{id}/heats/{heat_id}/start-list` | Bearer organizer+ | добавить участника |
| POST | `/api/v1/events/{id}/heats/{heat_id}/start-list/fill` | Bearer organizer+ | bulk из roster (optional category_id) |
| PATCH | `/api/v1/events/{id}/heats/{heat_id}/start-list/{entry_id}/status` | Bearer organizer+ | check-in / DNS / DNF / … |
| GET | `/api/v1/events/{id}/heats/{heat_id}/runs` | Bearer | runs (attempt) |
| GET | `/api/v1/events/{id}/results` | Bearer | results (`?status=`) |
| POST | `/api/v1/events/{id}/results` | Bearer organizer+ | upsert draft (score/place) |
| PATCH | `/api/v1/events/{id}/results/{result_id}/status` | Bearer organizer+ | draft\|verified\|published\|void |
| GET | `/api/v1/events/{id}/results/{result_id}/history` | Bearer | history/audit строки |
| GET | `/api/v1/events/{id}/officials` | Bearer | судьи |
| GET | `/api/v1/events/{id}/training-slots` | Bearer | слоты (`only_booked`, `discipline`) |
| GET | `/api/v1/events/{id}/schedule-hint` | Bearer | текстовая подсказка расписания |
| GET | `/api/v1/audit` | Bearer admin | audit |

## Rules & protocol (0.5.2)

| Method | Path | Auth | Описание |
|--------|------|------|----------|
| GET | `/api/v1/rules/catalog` | no | governing bodies, disciplines, rules packs, scoring modes |
| GET | `/api/v1/events/{id}/rules-profile` | Bearer | профиль правил (null если не задан) |
| PUT | `/api/v1/events/{id}/rules-profile` | Bearer organizer+ | создать/обновить профиль |
| GET | `/api/v1/events/{id}/protocol-captures` | Bearer | список фото/PDF протоколов (`?heat_id=`) |
| POST | `/api/v1/events/{id}/protocol-captures` | Bearer organizer+/judge | upload (multipart: file, title, kind?, heat_id?, notes?) |
| PATCH | `/api/v1/events/{id}/protocol-captures/{id}` | Bearer | status draft\|verified\|published\|rejected (verify — organizer+) |
| GET | `/api/v1/events/{id}/protocol-captures/{id}/file` | Bearer | скачать файл |

Kinds протокола: `judge_sheet`, `chief_protocol`, `photo_result`, `other`. Файлы: JPG/PNG/WebP/PDF ≤15 МБ.

| Method | Path | Auth | Описание |
|--------|------|------|----------|
| GET | `/api/v1/events/{id}/scoring/engine` | Bearer | meta движка по EventRulesProfile |
| GET | `/api/v1/events/{id}/judge-scores` | Bearer | листы судей (`?participant_id=` / `?heat_id=`) |
| POST | `/api/v1/events/{id}/judge-scores` | Bearer organizer+/judge | критерии → total |
| POST | `/api/v1/events/{id}/judge-scores/aggregate` | Bearer organizer+ | панель → result draft |

Ошибка:

```json
{ "error": { "code": "forbidden", "message": "..." } }
```

Подробности auth: `docs/OPERATIONS/AUTH_PHONE.md`  
Команды владельца: `docs/OPERATIONS/OWNER_COMMANDS.md`

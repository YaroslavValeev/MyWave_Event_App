# API Contract (Stage 1 + auth/competition)

Базовый URL: `/`

## Health

| Method | Path | Auth | Описание |
|--------|------|------|----------|
| GET | `/health` | no | liveness + db_ok |
| GET | `/ready` | no | readiness (503 если DB down) |
| GET | `/api/v1/roles` | no | список ролей (`chief_judge` с 0.5.9) |

## Auth

| Method | Path | Auth | Описание |
|--------|------|------|----------|
| POST | `/api/v1/auth/register` | no | регистрация (participant active; иначе pending) |
| GET | `/api/v1/auth/login-options` | no | `otp_required` / `password_required` (пароля нет) |
| POST | `/api/v1/auth/phone/login` | no | JWT по известному телефону, **только если OTP не обязателен**; роль из аккаунта |
| POST | `/api/v1/auth/phone/request-otp` | no | OTP на email + mail_outbox |
| POST | `/api/v1/auth/phone/verify-otp` | no | JWT при status=active |
| GET | `/api/v1/auth/approvals/pending` | Bearer organizer+ | очередь ролей (**без** token) |
| POST | `/api/v1/auth/approvals/{approval_id}/approve` | Bearer organizer+ | утвердить по id |
| POST | `/api/v1/auth/approvals/{approval_id}/reject` | Bearer organizer+ | отклонить по id |
| GET | `/api/v1/auth/approvals/{token}/approve` | no (email link) | HTML-форма подтверждения (без мутации) |
| GET | `/api/v1/auth/approvals/{token}/reject` | no (email link) | HTML-форма подтверждения (без мутации) |
| POST | `/api/v1/auth/approvals/{token}/confirm` | form `decision=approve\|reject` | мутация по email-ссылке |
| POST | `/api/v1/auth/dev-login` | no (dev/test only) | JWT bootstrap |
| GET | `/api/v1/me` | Bearer | текущий пользователь (`pending_claim_count`) |
| PATCH | `/api/v1/me` | Bearer | имя и/или телефон |
| GET | `/api/v1/me/athlete-links` | Bearer | предполагаемые/подтверждённые профили |
| POST | `/api/v1/me/athlete-links/{id}/confirm` | Bearer | подтвердить связь (OTP уже пройден) |
| POST | `/api/v1/me/athlete-links/{id}/reject` | Bearer | отклонить связь; чужой link_id → 404 |
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
| GET | `/api/v1/events` | optional | список; без токена — только published / registration_open / live / completed |
| POST | `/api/v1/events` | Bearer organizer+ | создать (optional `rules_profile`: governing_body, sanction_body, discipline_codes[], scoring_mode) |
| GET | `/api/v1/events/{id}` | optional | получить (гости — только публичные статусы) |
| PATCH | `/api/v1/events/{id}` | Bearer organizer+ | обновить |
| GET | `/api/v1/events/{id}/detail` | optional | сводка + counts (`roster_locked_at`) |
| POST | `/api/v1/events/{id}/roster/lock` | Bearer organizer+ | зафиксировать состав (идемпотентно; пустой → `400 roster_empty`) |
| POST | `/api/v1/events/{id}/roster/unlock` | Bearer organizer+ | снять фиксацию (audit `reason`) |

При `roster_locked_at != null`: новые заявки, accept, import commit, ingest-pack, scan-protocol → **409** `roster_locked`. Check-in / heats / scoring остаются.

## Competition

| Method | Path | Auth | Описание |
|--------|------|------|----------|
| GET | `/api/v1/events/{id}/categories` | optional | категории |
| GET | `/api/v1/events/{id}/participants` | Bearer | участники (**accepted/registered**, без phone; self-serve без publish-consent — псевдоним) |
| POST | `/api/v1/events/{id}/applications` | Bearer | подать заявку (registration_open) |
| GET | `/api/v1/events/{id}/applications/me` | Bearer | своя заявка |
| GET | `/api/v1/events/{id}/applications` | Bearer organizer+ | очередь заявок |
| PATCH | `/api/v1/events/{id}/applications/{participant_id}` | Bearer organizer+ | accept/reject |
| GET | `/api/v1/events/{id}/documents` | Bearer | документы |
| POST | `/api/v1/events/{id}/documents` | Bearer organizer+ | upload (multipart: file, title, kind, language?, description?, access_class?) |
| DELETE | `/api/v1/events/{id}/documents/{doc_id}` | Bearer organizer+ | удалить документ + файл |
| GET | `/api/v1/events/{id}/documents/{doc_id}/file` | Bearer | скачать файл |
| GET | `/api/v1/events/{id}/checklist` | Bearer | чеклист подготовки (auto-seed + auto-tick) |
| PATCH | `/api/v1/events/{id}/checklist/{item_id}` | Bearer organizer+ | `{"is_done": true\|false}` |
| GET | `/api/v1/events/{id}/heats` | optional | heats на публичном событии; start list — отдельно с Bearer |
| POST | `/api/v1/events/{id}/heats` | Bearer organizer+ | создать heat |
| PATCH | `/api/v1/events/{id}/heats/{heat_id}/status` | Bearer organizer+ | planned\|ready\|on_water\|completed\|cancelled |
| GET | `/api/v1/events/{id}/heats/{heat_id}/start-list` | Bearer | start list |
| POST | `/api/v1/events/{id}/heats/{heat_id}/start-list` | Bearer organizer+ | добавить участника |
| POST | `/api/v1/events/{id}/heats/{heat_id}/start-list/fill` | Bearer organizer+ | bulk из roster (optional category_id) |
| PATCH | `/api/v1/events/{id}/heats/{heat_id}/start-list/{entry_id}/status` | Bearer organizer+ | check-in / DNS / DNF / … |
| GET | `/api/v1/events/{id}/heats/{heat_id}/runs` | Bearer | runs (attempt) |
| GET | `/api/v1/events/{id}/results` | optional | results (`?status=`; гость — только published) |
| POST | `/api/v1/events/{id}/results` | Bearer organizer+/chief_judge | upsert draft (score/place) |
| PATCH | `/api/v1/events/{id}/results/{result_id}/status` | Bearer | `verified` — organizer+/chief_judge; `published` и void опубликованного — **только** `chief_judge` или `platform_admin` (`403 chief_approval_required`) |
| GET | `/api/v1/events/{id}/results/{result_id}/history` | Bearer | history/audit строки |
| GET | `/api/v1/events/{id}/officials` | optional | судьи |
| GET | `/api/v1/events/{id}/training-slots` | Bearer | слоты (`only_booked`, `discipline`) |
| GET | `/api/v1/events/{id}/schedule-hint` | optional | подсказка **этого** события (даты/город/слоты; бюллетень Казани — только для ЧР/ПР Казань) |
| GET | `/api/v1/audit` | Bearer admin | audit |

## Import Center (0.5.8)

| Method | Path | Auth | Описание |
|--------|------|------|----------|
| POST | `/api/v1/events/{id}/imports` | Bearer organizer+ | multipart `file` (.xlsx ≤5 МБ). Идемпотентно по SHA-256 |
| POST | `/api/v1/events/{id}/ingest-pack` | Bearer organizer+ | пакет файлов (xlsx+PDF) → состав IWWF + судьи + heats/start list + documents |
| POST | `/api/v1/events/{id}/scan-protocol` | Bearer organizer+ | сканы Казани + итоги поста ФВЛС → заезды, старты, **черновики** мест (Not homologated, без publish) |
| GET | `/api/v1/events/{id}/imports` | Bearer organizer+ | список пакетов |
| GET | `/api/v1/events/{id}/imports/{batch_id}` | Bearer organizer+ | пакет + строки (телефон маскирован) |
| PATCH | `/api/v1/events/{id}/imports/{batch_id}/rows/{row_id}` | Bearer organizer+ | `{"decision":"approve\|reject"}` |
| POST | `/api/v1/events/{id}/imports/{batch_id}/commit` | Bearer organizer+ | профили + pending_claim аккаунты + participants |

Повторная загрузка того же файла возвращает существующий пакет, без дубликатов. PII-файлы в GitHub не коммитятся.

## Rules & protocol (0.5.2)

| Method | Path | Auth | Описание |
|--------|------|------|----------|
| GET | `/api/v1/rules/catalog` | no | governing bodies, disciplines, rules packs, scoring modes |
| GET | `/api/v1/events/{id}/rules-profile` | Bearer | профиль правил (null если не задан) |
| PUT | `/api/v1/events/{id}/rules-profile` | Bearer organizer+ | создать/обновить профиль |
| GET | `/api/v1/events/{id}/protocol-captures` | Bearer | список фото/PDF протоколов (`?heat_id=`) |
| POST | `/api/v1/events/{id}/protocol-captures` | Bearer organizer+/judge | upload (multipart: file, title, kind?, heat_id?, notes?) |
| PATCH | `/api/v1/events/{id}/protocol-captures/{id}` | Bearer | status draft\|verified\|published\|rejected (verify — organizer+/chief; **published** — chief_judge/platform_admin) |
| GET | `/api/v1/events/{id}/protocol-captures/{id}/file` | Bearer | скачать файл |

Kinds протокола: `judge_sheet`, `chief_protocol`, `photo_result`, `other`. Файлы: JPG/PNG/WebP/PDF ≤15 МБ.

## Field moments (0.5.11, ADR-0011)

Полевые кадры для эфира (бэкстейдж / пилот / маршал), **не** official protocol. Гость и участник — 401/403. Файлы не на витрине.

| Method | Path | Auth | Описание |
|--------|------|------|----------|
| GET | `/api/v1/events/{id}/field-moments` | Bearer media/commentator/support/organizer+/chief_judge | список (`?heat_id=`) |
| POST | `/api/v1/events/{id}/field-moments` | Bearer те же роли | multipart: `file`, `title?`, `pov?`, `heat_id?`, `notes?` |
| PATCH | `/api/v1/events/{id}/field-moments/{id}` | Bearer | `title`/`pov`/`notes`; **status** draft\|approved\|withheld — только organizer+/chief_judge |
| GET | `/api/v1/events/{id}/field-moments/{id}/file` | Bearer те же роли, что GET списка | файл |

`pov`: `backstage` \| `boat_pilot` \| `start_marshal` \| `on_water` \| `crowd` \| `other`.  
Фото JPG/PNG/WebP/HEIC ≤15 МБ; видео MP4/WebM/MOV ≤40 МБ. Путь `data/field-media/{slug}/`.

| Method | Path | Auth | Описание |
|--------|------|------|----------|
| GET | `/api/v1/events/{id}/scoring/engine` | Bearer | meta движка по EventRulesProfile |
| GET | `/api/v1/events/{id}/judge-scores` | Bearer | листы судей (`?participant_id=` / `?heat_id=`) |
| POST | `/api/v1/events/{id}/judge-scores` | Bearer organizer+/judge | критерии → total |
| POST | `/api/v1/events/{id}/judge-scores/aggregate` | Bearer organizer+ | панель → result draft |

## Official protocol export (0.5.4)

| Method | Path | Auth | Описание |
|--------|------|------|----------|
| GET | `/api/v1/events/{id}/official-protocol` | Bearer organizer+ | JSON bundle + readiness |
| GET | `/api/v1/events/{id}/official-protocol/download` | Bearer organizer+ | attachment `.json` |
| GET | `/api/v1/events/{id}/official-protocol/html` | Bearer organizer+ | printable HTML |

## App downloads (0.5.10)

Публичный каталог выдачи. URL файлов только в env, не в ответе manifest/status.

| Method | Path | Auth | Описание |
|--------|------|------|----------|
| GET | `/api/v1/app-downloads/manifest` | no | метаданные приложения и 4 артефакта без target URL |
| GET | `/api/v1/app-downloads/{id}/status` | no | повторная проверка `android` \| `ios` \| `source` \| `documentation` |
| POST | `/api/v1/app-downloads/{id}/handoff` | no | validated `location` после подтверждения; 20 запросов/мин/IP |
| POST | `/api/v1/analytics/events` | no | ingest allowlisted событий (202) |

Состояния артефакта: `available` \| `unavailable` \| `error`. Пустой env или `{{...}}` → `unavailable`. Небезопасный URL → `error`. Handoff: `503 artifact_unavailable` / `artifact_misconfigured`, `429 too_many_requests`. Подключение файлов: `docs/OPERATIONS/APP_DOWNLOADS.md`.

## Athlete ID & archive (0.5.5)

- `User.athlete_id` — opaque `MW-XXXXXXXX` (без PII); канон 0.5.8 — `AthleteProfile.athlete_id`, аккаунт синхронизируется после confirm.
- `EventDetail.archived` — true при `completed` | `cancelled`.
- `Event.roster_locked_at` / `roster_locked_by_user_id` — фиксация состава (0.5.9, ADR-0008); не отдельный `Event.status`.
- Мутации на архивном событии → **409** `event_archived`.
- Исключение: `PATCH /api/v1/events/{id}/status` (можно вернуть в `live`).

Ошибка:

```json
{ "error": { "code": "forbidden", "message": "..." } }
```

Подробности auth: `docs/OPERATIONS/AUTH_PHONE.md`  
Команды владельца: `docs/OPERATIONS/OWNER_COMMANDS.md`

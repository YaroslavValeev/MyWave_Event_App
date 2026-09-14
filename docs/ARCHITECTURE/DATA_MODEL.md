# Модель данных — MyWave Event App

**Дата:** 2026-08-24  
**Владелец storage:** `services/api` (+ выбранный engine: SQLite / Postgres)

## 0. Stage 1 implementation note

Публичные id в runtime — **integer autoincrement**, не UUID. UUID остаётся целевым для внешних интеграций (TD-01). Ниже — логическая модель; колонки кода см. SQLAlchemy models.

### ConsentRecord (добавлено 2026-08-24)

| Поле | Тип | Обяз. | Описание |
|------|-----|-------|----------|
| id | int | ✓ | PK |
| user_id | int | ✓ | → User |
| purpose | string | ✓ | `terms_of_use` \| `privacy_policy` \| `publish_name_and_results` \| `product_analytics` |
| version | string | ✓ | версия документа, напр. `2026-08-24` |
| source | string | ✓ | `register` \| `profile` |
| granted_at | datetime | ✓ | |
| revoked_at | datetime | | null = активно |

История: при повторном grant предыдущая активная строка того же purpose закрывается `revoked_at`.

### AthleteProfile / AccountAthleteLink / ImportBatch (0.5.8)

**AthleteProfile** — SoT постоянного MyWave Athlete ID (`MW-XXXXXXXX`, без PII в самом ID): `display_name`, `latin_name`, `birth_year`, `region`.

**AthleteContact** — телефоны E.164, kind `self|guardian|representative`. Один телефон может относиться к нескольким профилям.

**AccountAthleteLink** — связь `User` ↔ профиль: `pending_claim` → `confirmed` | `rejected`. Нельзя автоматически объединять профили только по ФИО или телефону.

**ImportBatch / ImportRow** — staging импорта. Unique `(event_id, content_sha256)`. Статусы пакета: parsed → committed. Строка хранит исходный sheet/row, нормализованные поля, `match_kind` (`new|exact|probable|conflict|excluded`), `conflict_codes`, решение администратора. Медицинские URL в API и `raw_json` не кладём — только `has_medical`.

**Participant.athlete_profile_id** — связь roster с профилем. `user_id` может быть null (несколько дисциплин на событии).

**Document.access_class** — `public|participant|official|commentator|medical-restricted|consent-restricted|media-rights|admin-only`. Restricted классы не отдаются participant.

### Event roster lock / chief judge (0.5.9)

Runtime `Event` (integer PK): колонки `roster_locked_at`, `roster_locked_by_user_id` — фиксация состава без нового `status`. Роль `chief_judge` публикует official result; организатор делает draft/verified. См. ADR-0008.

### Notification (добавлено 2026-08-24)

| Поле | Тип | Обяз. | Описание |
|------|-----|-------|----------|
| id | int | ✓ | PK |
| user_id | int | ✓ | → User |
| kind | string | ✓ | `role.pending`, `application.submitted`, … |
| title | string | ✓ | |
| body | string | ✓ | |
| entity_type | string | | `user` / `participant` |
| entity_id | string | | |
| is_read | bool | ✓ | |
| created_at | datetime | ✓ | |

### EventChecklistItem (добавлено 2026-08-24)

| Поле | Тип | Обяз. | Описание |
|------|-----|-------|----------|
| id | int | ✓ | |
| event_id | int | ✓ | → Event |
| code | string | ✓ | documents / categories / officials / … |
| title | string | ✓ | |
| is_done | bool | ✓ | |
| sort_order | int | ✓ | |
| done_at | datetime | | |
| done_by_user_id | int | | → User |

SoT подготовки — в Event App, не на сайте.

### Heat / StartListEntry / Run (foundation, 2026-08-24)

**Heat** (≠ TrainingSlot): `event_id`, `category_id?`, `code`, `title`, `heat_number`, `scheduled_at?`, `status` (`planned`\|`ready`\|`on_water`\|`completed`\|`cancelled`).

**StartListEntry**: `heat_id`, `participant_id`, `start_order`, `bib_number?`, `status` (`scheduled`\|`checked_in`\|`ready`\|`on_water`\|`completed`\|`dns`\|`dnf`) + timestamps check-in/ready/on_water/completed.

**Run**: attempt для entry (`attempt_no`, sync status с entry при смене статуса).

Document upload пишет в существующую таблицу `documents` + файлы `data/documents/{slug}/`.


- Один SoT на инсталляцию приложения.
- UUID (строка) для публичных идентификаторов.
- Soft-delete опционально через `deleted_at`; для Stage 1 допустим hard-delete только админом с audit.
- Временные метки UTC ISO-8601.

## 2. Сущности Stage 1

### User

| Поле | Тип | Обяз. | Описание |
|------|-----|-------|----------|
| id | UUID | ✓ | PK |
| email | string | ✓* | уникальный; *или phone для будущего |
| display_name | string | ✓ | |
| password_hash | string | ✓ | Stage 1 password auth |
| is_active | bool | ✓ | |
| created_at / updated_at | datetime | ✓ | |

### Event

| Поле | Тип | Обяз. | Описание |
|------|-----|-------|----------|
| id | UUID | ✓ | |
| slug | string | ✓ | уникальный URL-ключ |
| title | string | ✓ | |
| description | text | | |
| starts_at / ends_at | datetime | ✓ | |
| venue | string | | |
| status | enum | ✓ | `draft`\|`published`\|`archived` |
| visibility | enum | ✓ | `public`\|`unlisted`\|`private` |
| settings_json | json | ✓ | флаги (judge_can_publish и т.д.) |
| created_by | UUID | ✓ | → User |
| created_at / updated_at | datetime | ✓ | |

### EventMembership

| Поле | Тип | Обяз. | Описание |
|------|-----|-------|----------|
| id | UUID | ✓ | |
| event_id | UUID | ✓ | |
| user_id | UUID | ✓ | |
| role | enum | ✓ | см. USER_ROLES |
| status | enum | ✓ | `invited`\|`active`\|`revoked` |
| created_at | datetime | ✓ | |

Уникальность: `(event_id, user_id, role)` или одна primary role на пользователя (решение реализации: Stage 1 — multi-role rows).

### Category

| Поле | Тип | Обяз. |
|------|-----|-------|
| id | UUID | ✓ |
| event_id | UUID | ✓ |
| code | string | ✓ |
| title | string | ✓ |
| sort_order | int | ✓ |

### Entry (заявка / участник в категории)

| Поле | Тип | Обяз. |
|------|-----|-------|
| id | UUID | ✓ |
| event_id | UUID | ✓ |
| category_id | UUID | ✓ |
| athlete_user_id | UUID | ✓ |
| team_name | string | |
| bib_number | string | |
| status | enum | ✓ | `draft`\|`submitted`\|`accepted`\|`rejected`\|`withdrawn` |
| created_at / updated_at | datetime | ✓ |

### Session (сессия / старт / heat)

| Поле | Тип | Обяз. |
|------|-----|-------|
| id | UUID | ✓ |
| event_id | UUID | ✓ |
| category_id | UUID | |
| title | string | ✓ |
| starts_at | datetime | |
| status | enum | ✓ | `planned`\|`live`\|`finished`\|`cancelled` |

### Result

| Поле | Тип | Обяз. |
|------|-----|-------|
| id | UUID | ✓ |
| event_id | UUID | ✓ |
| session_id | UUID | |
| entry_id | UUID | ✓ |
| judge_user_id | UUID | ✓ |
| payload_json | json | ✓ | дисциплинарно-специфичные поля |
| status | enum | ✓ | `draft`\|`submitted`\|`published`\|`void` |
| published_at | datetime | |
| version | int | ✓ | optimistic lock |
| created_at / updated_at | datetime | ✓ |

### Artifact

| Поле | Тип | Обяз. |
|------|-----|-------|
| id | UUID | ✓ |
| event_id | UUID | ✓ |
| kind | string | ✓ | `document`\|`media`\|`export` |
| storage_key | string | ✓ |
| content_type | string | ✓ |
| created_by | UUID | ✓ |
| created_at | datetime | ✓ |

### AuditEvent

| Поле | Тип | Обяз. |
|------|-----|-------|
| id | UUID | ✓ |
| actor_user_id | UUID | |
| event_id | UUID | |
| action | string | ✓ |
| entity_type / entity_id | string | ✓ |
| payload_json | json | |
| created_at | datetime | ✓ |

### ConsentRecord

| Поле | Тип | Обяз. |
|------|-----|-------|
| id | UUID | ✓ |
| user_id | UUID | ✓ |
| purpose | string | ✓ |
| version | string | ✓ |
| granted_at | datetime | ✓ |
| revoked_at | datetime | |

## 3. Связи (кратко)

```text
User 1—* EventMembership *—1 Event
Event 1—* Category 1—* Entry *—1 User(athlete)
Event 1—* Session
Entry 1—* Result
Event 1—* Artifact
User 1—* AuditEvent
User 1—* ConsentRecord
```

## 4. Что сознательно отсутствует на Stage 1

- Отдельная сущность `Run` оркестрации AI (это не Personal_Helper merge).
- Репликация в внешний сайт.
- Таблицы Telegram chat mapping (адаптер Stage 4).

## 5. Миграции

- Alembic в `services/api` (целевой стандарт).
- Bootstrap SQLite для local без Postgres.

# ADR-0013 — Event Publications (посты и новости)

Дата: 2026-11-03  
Статус: accepted  
Связь: ROADMAP Stage 5/7, ADR-0003, ADR-0012 (EventReport остаётся отдельным)

## Контекст

Champ App нуждается в ленте публикаций (пост/новость) с фото, привязкой к мероприятию и проверкой роли на сервере.  
Существующие сущности **не подходят** как SoT для ленты:

- `EventReport` — один нарративный отчёт на событие.
- `ProtocolCapture` — судейский протокол (фото/PDF), не контент ленты.
- `Result` — спортивный результат.

## Решение

1. Ввести отдельный домен **Publication** (+ `PublicationMedia`).
2. Типы: `post` | `news`.
3. Серверные статусы: `draft` | `pending_moderation` | `published` | `rejected` | `void`.
4. Клиентские статусы очереди (не в БД SoT): `queued` | `error`.
5. **Не создавать** роли «фотограф» / «редактор». Использовать capabilities поверх существующих ролей.
6. `author_role` в запросе обязан совпадать с текущей ролью пользователя; иначе 403.
7. Идемпотентность: `Idempotency-Key` / `idempotency_key` уникален в рамках `(event_id, author_user_id)`.
8. Медиа хранить под `DATA_DIR/publications/<event_slug>/` (уважать `DATA_DIR`).

### Capabilities (канон)

| Capability | Роли |
|------------|------|
| `create_post` | `media`, `commentator`, `organizer`, `federation_manager`, `event_admin`, `platform_admin` |
| `create_news` | `organizer`, `federation_manager`, `event_admin`, `platform_admin` |
| `publish_direct` | `organizer`, `federation_manager`, `event_admin`, `platform_admin` |
| `moderate` | то же, что `publish_direct` |
| `edit_own` / `delete_own` | автор (если не void) |
| `edit_any` / `delete_any` | `moderate` |

`media` / `commentator` при запросе публикации получают `pending_moderation`, пока модератор не опубликует.

## Последствия

- EventReport и ParserNews остаются отдельным контуром Stage 7.
- Photographer Mode (Stage 5 EXIF/heat-link) — последующее расширение поверх PublicationMedia, не замена.
- Offline-очередь клиента не заявляет «published», пока API не подтвердил.

## Откат

Удалить маршруты `/publications*`, таблицы `publications` / `publication_media`, UI вкладки «Лента». Соревновательное ядро не затрагивается.

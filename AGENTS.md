# AGENTS.md — MyWave Event App

Инструкция для AI-агентов и разработчиков в этом репозитории. Дата: 2026-09-15.

## Продукт

- **Имя:** MyWave Event App — standalone competition platform.
- **UI / продуктовая итерация:** Champ App UX/UI 1.0 — Role Based + Live First ([docs/PRODUCT/UX_UI_CANON.md](docs/PRODUCT/UX_UI_CANON.md)).
- **Альтернатива в глоссарии:** «FVLS × MyWave Competition Hub» — не переименовывать без владельца.
- **Не путать** с Download Center (`releases/download-center-2026-08-02/`) — это архив канала выдачи, не приложение.

## Обязательный канон

1. Читать [docs/CANONICAL_DOCS_INDEX.md](docs/CANONICAL_DOCS_INDEX.md) перед архитектурными изменениями.
2. Перед любыми изменениями UI читать: этот файл, `PRD.md`, `USER_ROLES_AND_JOURNEYS.md`, **`UX_UI_CANON.md`**, `CURRENT_STATE.md`.
3. Следовать ADR в `docs/ARCHITECTURE/decisions/`.
4. Соблюдать `.cursor/rules/*.mdc`.
5. **Язык пользовательского интерфейса — только русский.**  
   Весь production UI приложения должен быть на русском языке.  
   Английские строки допустимы только во внутренних идентификаторах, API, БД, source code и технических логах.  
   Любое техническое значение перед выводом пользователю преобразуется в русское presentation label (централизованно, напр. `apps/web/src/lib/labels.ts`).  
   AI-агентам и разработчикам **запрещено** добавлять новые английские пользовательские строки.
6. Не утверждать существование мобильных сборок, production deploy или готового offline MVP, если это не отражено в `docs/STATUS/CURRENT_STATE.md`.

## Границы системы

| Слой | Роль | Что делать | Чего не делать |
|------|------|------------|----------------|
| Product (docs + apps/web) | UX, роли, journeys | UI, copy, PWA shell | Не тащить Flask-сайт MyWave в ядро |
| API (services/api) | Source of truth данных соревнования | REST/OpenAPI, auth, бизнес-правила | Не дублировать SoT в клиенте |
| Shared schema | Контракты | Версионируемые модели | Не хардкодить схему только в UI |
| Адаптеры (позже) | Telegram/MAX/Site | Опциональные интеграции | Не делать их архитектурным ядром |
| releases/ | Архив дистрибуции | Хранить артефакты выдачи | Не разворачивать как основное приложение |

## Оркестратор и слои (кратко)

- **Единственный source of truth:** API + БД этого репозитория.
- **Оркестрация домена:** backend `services/api` (use-cases / services layer).
- Клиент (`apps/web`) — presentation; не принимает финальные бизнес-решения.
- UX/UI redesign **не** требует переписывания backend без объективной необходимости.

Подробнее: [ADR-0003](docs/ARCHITECTURE/decisions/ADR-0003-orchestrator-and-layers.md).

## Workflow агента

1. Обновить статус/долг в `docs/STATUS/`, если меняется реальность продукта.
2. Сначала контракты/доки → затем код.
3. При противоречии кода и канона — явно зафиксировать расхождение; исправить код или обновить доку после продуктового решения. Не менять UX-модель молча.
4. Секреты не писать в файлы; только `.env.example`.
5. Для server deploy — только команды из [SERVER_COMMANDS.md](docs/OPERATIONS/SERVER_COMMANDS.md) для **этого** standalone app.
6. Не применять patch Download Center к этому репо как к «главному коду приложения».

## Stage 1 tech stack

- Backend: Python 3.11+, FastAPI, SQLAlchemy/SQLite (Postgres optional).
- Frontend: Next.js (App Router) + TypeScript, PWA-ready.
- Auth Stage 1: session/JWT в API (уточняется в SECURITY.md).
- Compose: `docker-compose.yml` — api + web; profile `postgres` опционален.

## Координация

См. [docs/AI_AGENT_OPERATING_MODEL.md](docs/AI_AGENT_OPERATING_MODEL.md) и правило `.cursor/rules/70-agent-coordination.mdc`.

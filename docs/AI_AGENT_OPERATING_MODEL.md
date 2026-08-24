# AI Agent Operating Model

Дата: 2026-08-24  
Продукт: MyWave Event App (не Personal_Helper / Agents / Molt).

Lead Orchestrator управляет Product, Architect, Backend, Frontend, Security, QA, DevOps, Docs агентами. Параллелить только независимые области файлов.

## Ownership

| Область | Путь |
|---------|------|
| Web | `apps/web/**` |
| API | `services/api/**` |
| Schema | `packages/shared-schema/**` |
| Docs | `docs/**` |
| Archive | `releases/**` (read-only по умолчанию) |
| Legal texts | `docs/LEGAL/**` + `services/api/app/domain/consent.py` |

## Правила subagents / worktrees

1. Параллельные агенты не пишут в один файл (ни SoT-документ, ни модуль API).
2. Независимые задачи — отдельные worktrees/ветки или заранее закреплённые пути.
3. Перед merge Lead проверяет diff, архитектуру, тесты и documentation transaction.
4. Не создавать дубликаты канонических документов под другими именами.

## Documentation transaction

Критичное изменение незавершено, пока в том же цикле не обновлены соответствующие канонические документы (см. матрицу в master prompt / `CANONICAL_DOCS_INDEX.md`). Решение только в чате считается непринятым.

## Definition of Done

По `AGENTS.md`: код + тесты + docs, без секретов, без fake APK/IPA, без утверждений Stage 2+/mobile без фактов в `CURRENT_STATE.md`.

## Обязательные проверки цикла

- pytest `services/api`
- web build, если менялся `apps/web`
- не называть unavailable проверки passed

## Handoff

Формат: сделано / pending / риски / следующий P0. Ссылки на пути в репозитории, не на внутренние рассуждения.

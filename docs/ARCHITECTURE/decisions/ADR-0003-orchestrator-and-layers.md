# ADR-0003: Orchestrator and layers

**Дата:** 2026-08-04  
**Статус:** Accepted  

## Контекст

Нужно явно назвать, кто оркестрирует доменные процессы (создание события → роли → заявки → результаты → публикация), чтобы не плодить «вторых мозгов» в Web, Telegram или сайте.

## Решение

1. **Source of Truth:** БД за `services/api`.
2. **Domain orchestrator (Stage 1):** application/services layer внутри `services/api`.
3. **Presentation:** `apps/web` — UI, валидация форм, кэш; без финальных бизнес-решений.
4. **Adapters (позже):** Telegram/MAX/Site — вызывают API; не оркестрируют сами.
5. **Policy:** permission checks в API (и позже shared-policy package); не только в промптах/UI.

Слои:

```text
[Web / Adapters]
        │  HTTP /api/v1
        ▼
[API routers]
        ▼
[Use-cases / Services]  ← единый оркестратор домена
        ▼
[Repositories] → [DB]
```

## Последствия

- Один lifecycle Event/Entry/Result.
- Запрет двух независимых task engines для одного события.
- AI-агенты в Cursor помогают коду, но не становятся runtime-оркестратором продукта.

## Альтернативы (отложены)

- Выделение отдельного `services/orchestrator` microservice — premature для Stage 1.
- Client-side orchestration с «толстым» браузером — риск расхождения правил.

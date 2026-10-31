# ADR-0012: Event reporting — Live ops, sparse moments, human-approved draft

Дата: 2026-10-27  
Статус: accepted  
Связано: [EVENT_REPORTING_MODEL.md](../../PRODUCT/EVENT_REPORTING_MODEL.md), [KAZAN_VIRTUAL_DRY_RUN.md](../../PRODUCT/KAZAN_VIRTUAL_DRY_RUN.md)

## Контекст

Нужна отчётность о соревновании без второго Excel и без обязательного штатного репортёра. Варианты:

1. Всё писать Live как статью — неудобно на воде.
2. Всё писать после дня с нуля — теряются факты, дублируется SoT.
3. Отдельный человек весь день только на отчёт — дорого и создаёт второй контур.
4. AI сам публикует — риск ложного нарратива и обхода ролей.

## Решение

**Dual-track:**

1. **Operational facts** вводятся Live владельцами ролей (уже Event App SoT: heats, results, checklist).
2. **Sparse moments** (фото/видео/короткая заметка/голос→текст) — опционально Live; в отчёт только после moderate approve.
3. **EventReport** собирается **после** heat/дня: по умолчанию **AI draft** (`ENABLE_EVENT_REPORT_LLM=1`): local heuristic всегда; OpenAI — если задан `OPENAI_API_KEY`. Template — `use_llm=false`. Только `draft` до human publish.
4. **Publish** — только человек (`organizer` / `event_admin` / `federation_manager` / `platform_admin`; commentator может edit draft, publish — organizer+).
5. **Excel** — выгрузка (`GET .../event-report/excel`) как производный артефакт, **не SoT**.
6. **Физические handoff** между ролями канонизированы в `role_physical_actions` + `GET .../role-actions`.

Границы:

| Действие | Template/AI | Человек |
|----------|-------------|---------|
| Цифры результатов | читает SoT | судья/организатор уже ввели |
| Текст хроники | предлагает draft | правит |
| Publish report | запрещён | обязателен |
| Судейство / void result | запрещён | существующие роли |

STT (`ENABLE_EVENT_REPORT_STT`) пишет только в заметку момента/report note, не в scores.

## Последствия

- SoT цифр остаётся `results` / start list; EventReport хранит `facts_json` снимок + редактируемый `body_markdown`.
- ParserNews / эфир читают только `published` report.
- Telegram не становится оркестратором отчёта (ADR-0001 / ADR-0003).
- Первый инкремент кода: assemble template без внешнего LLM.

## Отклонённые альтернативы

- Excel-отчёт как SoT (разрешена только выгрузка из App).
- AI auto-publish.
- Обязательная роль «reporter» в штате события.

## Инкремент 0.5.9

- AI assemble включён по умолчанию (local + optional OpenAI).
- Excel export + матрица физических действий / handoff.

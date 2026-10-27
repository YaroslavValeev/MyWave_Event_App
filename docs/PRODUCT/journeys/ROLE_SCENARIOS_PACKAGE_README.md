# MyWave Event App — пакет ролевых сценариев

## Назначение

Этот пакет передается команде разработчиков и Lead AI Agent в Cursor. Он описывает целевые пользовательские пути MyWave Event App / Champ App и порядок превращения их в рабочую систему проведения соревнований.

## Состав

- `participant_journey_event_app.md` — участник/спортсмен.
- `organizer_journey_event_app.md` — организатор.
- `judge_scorer_journey_event_app.md` — судья, chief judge, скорер, homologator.
- `photographer_videographer_journey_event_app.md` — фотограф, видеограф, media manager.
- `host_commentator_journey_event_app.md` — ведущий и комментатор.
- `volunteer_journey_event_app.md` — волонтеры и координатор.
- `technical_director_journey_event_app.md` — технический директор и подчиненные.
- `boat_captain_journey_event_app.md` — капитан/водитель катера.
- `broadcast_director_journey_event_app.md` — режиссер трансляции.
- `additional_roles_and_journeys_event_app.md` — карта дополнительных ролей.
- `cursor_ai_agents_role_implementation_brief.md` — письмо-инструкция команде AI Agents в Cursor.

## Как использовать в Cursor

1. Передать весь архив Lead AI Agent.
2. Попросить прочитать сначала `cursor_ai_agents_role_implementation_brief.md`.
3. Затем прочитать все role journey документы.
4. Выполнить repository audit.
5. Сопоставить фактический код со сценариями.
6. Выбрать P0 vertical slice.
7. Реализовать code + tests + docs + Validation Report.

## Первый P0-срез

`create event → registration → review → roster lock → one heat → check-in → score → chief judge approval → official result → protocol → archive`.

## Важные ограничения

- БД приложения — Source of Truth.
- Excel используется только для импорта/экспорта.
- Athlete ID не содержит ФИО, телефон и дату рождения.
- Draft score отделен от official result.
- AI не принимает спортивные, медицинские, финансовые и чувствительные решения самостоятельно.
- Массовая рассылка, scoring, публикация результата и corrections требуют human approval.
- Production не меняется без backup, migration и rollback.
- В архиве не должно быть приватных документов и неразрешенных медиа.

## Текущая оговорка

GitHub `YaroslavValeev/MyWave_Event_App` **доступен** (public). Эти файлы — **целевые сценарии**, не описание уже готового UI. Сверка с кодом: [ROLE_JOURNEYS_RECONCILIATION.md](../../STATUS/ROLE_JOURNEYS_RECONCILIATION.md). P0-срез 0.5.9: roster lock + публикация только `chief_judge`.

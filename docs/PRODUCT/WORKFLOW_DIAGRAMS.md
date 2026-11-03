# Workflow Diagrams — Champ App (Agent 12)

Дата: 2026-11-04  
Статус: каталог процессов, согласованный с фактическим кодом + целевыми расширениями 0.5.17  
Роли в коде: см. `services/api/app/domain/roles.py`  
Схемы — Mermaid flowchart; экспорт SVG/PNG — через IDE/CI при наличии mermaid-cli (не обязателен для runtime).

Легенда: прямоугольник = шаг; ромб = решение; «API» = серверная операция; «local» = клиент.

## Схема A — Роли и доступ

```mermaid
flowchart TD
  A[Вход в Champ App] --> B{JWT валиден?}
  B -->|Нет| C[OTP / повторный вход]
  C --> A
  B -->|Да| D[API: загрузить user.role]
  D --> E{Роль active?}
  E -->|pending/rejected| F[Ожидание / гость]
  E -->|Да| G[Ролевые вкладки события]
  G --> H[Выбрать действие]
  H --> I{API AuthZ}
  I -->|403| J[Показать причину]
  J --> G
  I -->|OK| K[Выполнить + audit]
  K --> L[Результат]
```

## Схема B — Организатор

```mermaid
flowchart TD
  A[Создать событие draft] --> B[Правила / категории / документы]
  B --> C[Назначить official / approvals]
  C --> D{Checklist готов?}
  D -->|Нет| B
  D -->|Да| E[registration_open]
  E --> F[Заявки / roster]
  F --> G[Heats / start lists]
  G --> H[status live]
  H --> I[Контроль судейства]
  I --> J{Results verified?}
  J -->|Нет| I
  J -->|Да| K[Publish results]
  K --> L[Утвердить ревизию протокола]
  L --> M[EventReport / archive completed]
```

## Схема C — Участник (participant)

```mermaid
flowchart TD
  A[Регистрация + согласия] --> B[Выбор события]
  B --> C[Подать заявку API]
  C --> D{accepted?}
  D -->|Нет| E[Уведомление / правка]
  E --> C
  D -->|Да| F[Слоты / документы / старты]
  F --> G[Участие]
  G --> H[Смотреть scoreboard / results]
  H --> I[Итоги published]
```

## Схема D — Судья

```mermaid
flowchart TD
  A[Роль judge утверждена] --> B[Открыть событие]
  B --> C[Вкладка Судейство]
  C --> D[Выбрать участника / heat]
  D --> E[Ввод критериев 0..100]
  E --> F{Валидация}
  F -->|Нет| E
  F -->|Да| G[API POST judge-scores]
  G --> H[Опционально protocol-capture]
  H --> I[Передать organizer verify/publish]
```

## Схема E — Online Scoring

```mermaid
flowchart TD
  A[JudgeScore / Result draft] --> B[Aggregate по EventRulesProfile]
  B --> C[Result draft]
  C --> D{Organizer verify?}
  D -->|Нет| E[Коррекция + ResultHistory]
  E --> C
  D -->|Да| F[verified]
  F --> G[published]
  G --> H[Scoreboard revision]
  H --> I[SSE / polling UI]
```

## Схема F — Протоколы

```mermaid
flowchart TD
  A[Live official-protocol preview] --> B{Readiness OK?}
  B -->|Нет| C[Закрыть blockers]
  C --> A
  B -->|Да| D[POST official-protocol/revisions]
  D --> E[Immutable snapshot + sha256]
  E --> F[Download JSON ревизии]
  F --> G[При коррекции results → новая ревизия]
```

## Схема G — Online / Offline

```mermaid
flowchart TD
  A[Действие пользователя] --> B{navigator.onLine + API?}
  B -->|Да| C[HTTP + Idempotency-Key]
  C --> D{2xx / 409 / timeout}
  D -->|2xx| E[Подтверждено сервером]
  D -->|409| F[Показать конфликт]
  D -->|timeout| G[local queued]
  B -->|Нет| G
  G --> H[Восстановление сети]
  H --> C
```

## Схема H — Публикация контента

```mermaid
flowchart TD
  A[Лента события] --> B[Камера / галерея]
  B --> C[Текст + author_role]
  C --> D{API RBAC}
  D -->|403| E[Ошибка роли]
  D -->|OK| F{intent publish}
  F -->|media/commentator| G[pending_moderation]
  F -->|organizer+| H[published]
  G --> I[Staff moderate]
  I --> H
  H --> J[Лента]
```

## Схема I — Жизненный цикл

```mermaid
flowchart TD
  A[DRAFT] --> B[CONFIGURED]
  B --> C[REGISTRATION]
  C --> D[READY]
  D --> E[LIVE]
  E --> F[RESULTS_REVIEW]
  F --> G[OFFICIAL]
  G --> H[ARCHIVED]
```

`journey_phase` вычисляется поверх `EventStatus` (ADR-0015), статусы API не ломаются.

## Role × Action × State (фактические роли кода)

| Роль | Prep | Live | After |
|------|------|------|-------|
| organizer / event_admin / federation_manager / platform_admin | событие, checklist, approvals | verify/publish, scoreboard staff | protocol revision, report, archive |
| judge | назначение | judge-scores, protocol-capture | свои листы |
| participant | заявка, согласия | статус, табло | published results |
| media / commentator | — | лента постов, report edit | черновики отчёта |
| support | — | participants/docs | — |
| guest / public | витрина | scoreboard published | published results |

Нет отдельных ролей «главный судья / секретарь / тренер» в API — capabilities через organizer+/judge/participant.

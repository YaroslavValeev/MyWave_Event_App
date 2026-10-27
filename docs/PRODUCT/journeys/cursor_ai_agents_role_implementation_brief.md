# MyWave Event App — письмо команде AI Agents в Cursor

**Адресаты:** Lead AI Agent, subagents и разработчики MyWave Event App / Champ App  
**Дата:** 14.09.2026  
**Цель:** превратить ролевые сценарии в рабочую платформу проведения соревнований

## 1. Задача команды

Команда должна реализовать не набор демонстрационных экранов, а единую систему проведения соревнования:

`подготовка → приглашение → регистрация → допуск → roster → расписание → check-in → heats → scoring → результаты → медиа → трансляция → архив`.

Главный критерий продукта: хотя бы одно реальное соревнование проводится без Excel как основного Source of Truth.

Ролевые документы из этого архива являются целевыми сценариями. Они должны быть сопоставлены с текущим кодом, моделями, API и документацией. Нельзя утверждать, что функция готова, если она не проверена в репозитории и тестовом прогоне.

## 2. Документы, обязательные к прочтению

1. `participant_journey_event_app.md`
2. `organizer_journey_event_app.md`
3. `judge_scorer_journey_event_app.md`
4. `photographer_videographer_journey_event_app.md`
5. `host_commentator_journey_event_app.md`
6. `volunteer_journey_event_app.md`
7. `technical_director_journey_event_app.md`
8. `boat_captain_journey_event_app.md`
9. `broadcast_director_journey_event_app.md`
10. `additional_roles_and_journeys_event_app.md`

## 3. Что нужно сделать в первую очередь

### Шаг 1. Repository audit

Проверить фактическое состояние репозитория:

- ветка и commit;
- remote и GitHub доступ;
- стек и структура;
- frontend/backend/database;
- auth/OTP;
- роли и permissions;
- event/application/roster/documents;
- officials/notifications/audit;
- tests, lint, typecheck, build;
- CI/CD, staging и production;
- незакоммиченные изменения;
- расхождения между кодом и документацией.

Если репозиторий или нужная ветка недоступны, зафиксировать это как блокер и не выдумывать результат аудита.

### Шаг 2. Reconciliation

Сопоставить существующий код с ролевыми документами и разделить результаты:

- реализовано;
- реализовано частично;
- отсутствует;
- противоречит принятой архитектуре;
- заблокировано окружением;
- требует решения владельца.

Не создавать дубликаты моделей и модулей. Сначала найти существующие `event`, `participant`, `application`, `document`, `official`, `notification`, `audit` и расширять их миграциями.

### Шаг 3. Выбрать P0 vertical slice

Если в CURRENT_STATE или ROADMAP уже есть утвержденная задача — продолжить ее. Если нет, реализовать:

`create event → registration → review → roster lock → one heat → check-in → score → chief judge approval → official result → protocol → archive`.

Медиа, broadcast и расширенная автоматизация подключаются после стабилизации этого среза.

## 4. Обязательная ролевая модель AI Agents

### Lead Orchestrator

Отвечает за:

- понимание задачи и репозитория;
- план и декомпозицию;
- назначение subagents;
- предотвращение конфликтов;
- интеграцию изменений;
- проверку diff;
- тесты и документацию;
- финальный отчет и handoff.

Lead Orchestrator не делегирует бездумно всю работу и лично проверяет критические документы, архитектуру и Definition of Done.

### Product / UX Agent

Отвечает за:

- user journeys;
- acceptance criteria;
- mobile-first UX;
- accessibility;
- states: loading, success, error, retry, offline, expired, permission denied;
- связь экранов с ролями;
- отсутствие лишних действий.

### Solution Architect

Отвечает за:

- границы модулей;
- API contracts;
- data flow;
- event lifecycle;
- Athlete ID;
- scoring/result model;
- offline strategy;
- ADR и технический долг.

### Backend / API Agent

Отвечает за:

- endpoints;
- validation;
- RBAC;
- idempotency;
- retries/timeouts;
- background jobs;
- audit events;
- storage adapters;
- contract tests.

### Database Agent

Отвечает за:

- PostgreSQL/SQLite compatibility;
- schema и migrations;
- constraints;
- indexes;
- Athlete ID uniqueness;
- event/heat/run/result consistency;
- backup/restore;
- отсутствие destructive migrations без rollback.

### Frontend / PWA Agent

Отвечает за:

- routing;
- state management;
- mobile-first participant mode;
- organizer desktop mode;
- judge/scorer mode;
- volunteer mode;
- offline states;
- responsive 320/390/tablet/desktop;
- keyboard and screen reader support.

### Mobile Agent

Отвечает за Capacitor/native shell, push, QR, camera, file access, deep links и secure storage только после готовности web/PWA foundation. Не создавать фиктивные APK/AAB/IPA.

### AI / Automation Agent

Отвечает за:

- triage;
- draft messages;
- data quality warnings;
- media match suggestions;
- archive completeness;
- structured outputs;
- prompt/version management;
- evaluations и observability.

AI не принимает решения о допуске, судействе, scoring, DSQ, апелляции, публикации результата, массовой рассылке или удалении данных.

### Security / Privacy Agent

Отвечает за:

- secrets/env;
- PII;
- consent;
- least privilege;
- signed URLs;
- uploads;
- audit;
- retention/delete;
- negative access tests;
- dependency audit.

### QA / Accessibility Agent

Отвечает за:

- unit/integration/contract/e2e;
- permission tests;
- offline/reconnect/conflict;
- double submit;
- expired token;
- invalid file;
- responsive viewports;
- keyboard/accessibility;
- startup smoke и release verification.

### DevOps / Release Agent

Отвечает за:

- Docker/CI;
- environments;
- migrations;
- health checks;
- monitoring;
- backup;
- rollback;
- runbook;
- release artifacts;
- staging.

### Technical Writer / Documentation Agent

Отвечает за актуальность README, PRD, API, DATA_MODEL, SECURITY, TESTING, RUNBOOK, CURRENT_STATE, CHANGELOG, ADR и Validation Report. Lead Orchestrator лично проверяет итоговые документы.

## 5. Ownership областей

| Область | Владелец | Согласует |
|---|---|---|
| Event/application/roster | Backend + Database | Product, Security |
| Athlete ID | Architect + Database | Security, Product |
| Heat/start list/run | Backend + Scoring | Chief judge, Product |
| Results/protocol | Scoring + Backend | Chief judge, Federation |
| Participant UX | Frontend/PWA | Product, Accessibility |
| Organizer UX | Frontend/PWA | Event manager |
| Judge/scorer UX | Frontend + Scoring | Chief judge |
| Media | Media module owner | Security, consent owner |
| Broadcast | Broadcast integration owner | Director, TD |
| Volunteer | Product + Frontend | Event coordinator |
| Infrastructure | DevOps/SRE | TD, Security |
| Documentation | Technical Writer | Lead Orchestrator |

Два agents не изменяют один и тот же файл параллельно без заранее согласованного ownership.

## 6. Непереговорные архитектурные правила

1. БД приложения — Source of Truth.
2. Excel — только импорт/экспорт, не live database.
3. Event ID связывает событие и его данные.
4. Athlete ID постоянный и не содержит ФИО, телефон или дату рождения.
5. Official result отделен от draft score.
6. `ввод → проверка → approval → publish → archive`.
7. Все критические действия имеют audit trail.
8. Роли проверяются на API, не только в UI.
9. Медицинские и финансовые данные не попадают в public/coach/commentator/media interfaces без необходимости.
10. Массовые сообщения требуют human approval.
11. AI не заменяет судью, chief judge, event director, safety lead или владельца продукта.
12. Offline операции имеют idempotency key и conflict resolution.
13. Публикация результата создает неизменяемый snapshot.
14. Архив после `completed` — read-only.
15. Production не изменяется без подтвержденного backup, migration и rollback.

## 7. Требования к ролевым интерфейсам

### Участник

Приглашение, OTP, выбор события/категории, анкета, платежи, документы, consent, roster, тайминг, check-in, heat, результаты, апелляция, фото/видео, feedback, архив.

### Организатор

Паспорт, категории, документы, дедлайны, регистрация, review, roster, officials, schedule, heats, incidents, communications, scoring coordination, media, archive.

### Судья/скорер

Scoring schema, current heat, judge entry, draft, calculation, warnings, chief judge review, lock, publish, correction.

### Фотограф/видеограф

Roster, Athlete ID, heat, фактическое время, upload, EXIF/timecode, match review, consent, personal album, broadcast package.

### Ведущий

Verified profile, current/next heat, official result, pronunciation, approved media, delay wording, rundown, sponsor cues.

### Волонтер

Shift, zone, training, check-in, task checklist, supervisor, incident, handover, feedback.

### Технический директор

Health, release, DB, scoring, network, media, broadcast, backup, incidents, rollback.

### Капитан катера

Heat, order, ready, on-water, actual time, hold, interruption, emergency.

### Режиссер трансляции

Current/next, graphics, replay, approved media, sponsor cues, delay, backup feed, эфирный log.

## 8. Workflow в Cursor

Каждая задача выполняется так:

1. Read existing code/docs first.
2. Назвать точный scope и ownership.
3. Зафиксировать assumptions.
4. Обновить план и acceptance criteria.
5. Реализовать небольшой vertical slice.
6. Добавить schema/API/UI/tests.
7. Проверить security и accessibility.
8. Обновить канонические документы в той же задаче.
9. Запустить доступные проверки.
10. Проверить diff и чужие изменения.
11. Сформировать Validation Report.
12. Подготовить commit/patch и rollback instructions.

## 9. Definition of Done для любой задачи

Задача не считается завершенной без:

- кода;
- валидации ошибок;
- permissions;
- idempotency для повторяемых действий;
- тестов;
- accessibility для пользовательского UI;
- документации;
- audit для критических действий;
- обновленного CURRENT_STATE/CHANGELOG;
- точного результата проверок;
- списка оставшихся блокеров.

Нельзя писать `passed`, если проверка не запускалась. В таком случае писать `unavailable` и указывать причину.

## 10. Обязательные тестовые сценарии

- повторный submit и двойное нажатие;
- OTP retry и expired session;
- duplicate Athlete ID;
- один телефон для нескольких профилей;
- смена категории;
- лист ожидания;
- failed/pending/refunded payment;
- invalid/oversized/private file;
- недопустимый доступ к чужому документу;
- offline queue и reconnect;
- sync conflict;
- DNS/DNF/DSQ;
- correction до lock;
- correction после publish;
- результат без chief judge approval;
- апелляция с истекшим сроком;
- reported media;
- delay/change schedule;
- no-show volunteer;
- emergency escalation;
- rollback;
- backup restore.

## 11. Analytics и наблюдаемость

Для каждого нового сценария определить event taxonomy до реализации. Не отправлять PII и медицинские данные.

Минимальные бизнес-метрики:

- invite → OTP → application activation;
- application completion;
- payment success;
- document approval time;
- roster acceptance;
- check-in rate;
- time from heat start to official result;
- media delivery rate;
- feedback completion;
- volunteer no-show;
- incident response;
- offline conflict rate.

Минимальные технические метрики:

- API error/latency;
- queue depth;
- database locks;
- push delivery;
- upload failures;
- sync conflicts;
- backup age;
- rollback time;
- uptime during live.

## 12. Документационная транзакция

При изменении продукта команда обязана обновить соответствующие документы в той же задаче:

| Изменение | Обновить |
|---|---|
| UI/сценарий | PRD, CURRENT_STATE, CHANGELOG |
| API | API_CONTRACT, CHANGELOG, tests |
| Schema/migration | DATA_MODEL, migration notes, RUNBOOK |
| Role/permission | SECURITY, PRD, API |
| Offline | OFFLINE_SYNC, ADR, TESTING |
| Deployment/env | README, RUNBOOK, SECURITY |
| Архитектура | ARCHITECTURE, ADR |
| Известный блокер | CURRENT_STATE, TECH_DEBT |

## 13. План первых итераций

### Итерация 1: foundation

- repository audit;
- commit/tag текущего состояния;
- remote/CI/staging;
- environment validation;
- health API;
- RBAC и audit foundation;
- Athlete ID.

### Итерация 2: event preparation

- event passport;
- categories;
- documents upload/versioning;
- applications;
- payments status;
- review;
- roster lock.

### Итерация 3: competition day

- officials;
- schedule;
- heats;
- start lists;
- check-in;
- run status;
- DNS/DNF/DSQ.

### Итерация 4: results

- judge entry;
- calculation schema;
- chief judge review;
- lock;
- official publish;
- protocol;
- correction/appeal.

### Итерация 5: archive and media

- completed/read-only;
- secure media ingest;
- manual Athlete ID matching;
- personal album;
- feedback;
- broadcast package.

## 14. Письмо, которое можно вставить в Cursor Lead Agent

```text
Ты — Lead Orchestrator команды MyWave Event App. Сначала изучи репозиторий и существующую документацию. Не выдумывай реализованный функционал. Найди текущие модели, API, роли, migrations, tests и незакоммиченные изменения.

Используй документы participant_journey_event_app.md, organizer_journey_event_app.md, judge_scorer_journey_event_app.md, photographer_videographer_journey_event_app.md, host_commentator_journey_event_app.md, volunteer_journey_event_app.md, technical_director_journey_event_app.md, boat_captain_journey_event_app.md и broadcast_director_journey_event_app.md как целевые user journeys.

Сформируй reconciliation: implemented / partial / missing / contradictory / blocked / owner decision. Не создавай дубликаты существующих модулей.

При отсутствии утвержденной задачи реализуй P0 vertical slice:
create event → registration → review → roster lock → one heat → check-in → judge score → scorer calculation → chief judge approval → official result → protocol → archive.

Распредели только независимые задачи между Product/UX, Architect, Backend/API, Database, Frontend/PWA, Security, QA, DevOps и Documentation agents. Не допускай двум agents одновременное редактирование одного файла.

Обязательные правила: PostgreSQL/БД приложения — Source of Truth; Excel только import/export; Athlete ID не содержит PII; official result отделен от draft; maker-checker; audit log; RBAC на API; offline idempotency/conflicts; human approval для scoring, публикаций, массовых сообщений и чувствительных действий; AI не заменяет судью или event director.

Каждая задача должна включать code, validation, tests, security, accessibility, docs и Validation Report. Запусти все доступные lint/typecheck/tests/build/smoke/security/accessibility проверки. Если проверка недоступна, укажи unavailable и точную причину.

Не меняй production и не выполняй destructive migration без backup/rollback. Не создавай фиктивные APK/AAB/IPA. В конце предоставь фактический статус, changed files, tests, blockers, patch/commit, runbook commands и следующий конкретный шаг.
```

## 15. Финальный результат, который команда должна передать владельцу

- фактический repository audit;
- карта реализованных и отсутствующих функций;
- вертикальный P0 slice;
- код и migrations;
- API/UI/tests;
- security/accessibility checks;
- обновленные PRD, architecture, data model, API, security, testing, runbook и current state;
- Validation Report;
- release notes;
- patch/commit;
- команды staging/production с rollback;
- один список реальных blockers.

Главное правило: код, архитектура, ролевой сценарий, права, тесты и документация изменяются как единая транзакция. Результат, оставшийся только в чате, не считается принятым.

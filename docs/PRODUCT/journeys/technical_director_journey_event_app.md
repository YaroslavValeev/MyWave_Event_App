# MyWave Event App — сценарий технического директора и технической команды

**Дата:** 14.09.2026  
**Статус:** целевая спецификация для реализации и проверки  
**Роль:** технический директор соревнования (Technical Director / TD)

## 1. Назначение

Технический директор отвечает за готовность цифрового и физического технического контура соревнования: Event App, scoring, check-in, сеть, устройства, трансляция, данные, резервирование и восстановление.

Он не подменяет event director, chief judge, капитана катера или режиссера. Его задача — обеспечить, чтобы каждая команда могла выполнять свою работу на основании актуальных данных и чтобы сбой не превращался в потерю результатов.

## 2. Состав технической команды

| Роль | Зона ответственности |
|---|---|
| Technical Director | Архитектура, readiness, приоритеты, решения при техническом инциденте |
| Platform/API lead | API, бизнес-логика, auth, permissions, idempotency |
| Frontend/PWA lead | Web/PWA, мобильные экраны, offline UX, accessibility |
| Database/Data lead | Схема, миграции, backup, consistency, протоколы |
| DevOps/SRE | Deployment, health checks, logs, monitoring, rollback |
| Scoring systems operator | Judge/scorer devices, calculation, publish pipeline |
| Network/infra operator | Wi-Fi/LTE, резервный канал, VLAN/сегментация, power |
| Broadcast/graphics engineer | Live data feed, lower thirds, replay, routing |
| Device support | Планшеты, телефоны, зарядка, QR, периферия |
| Security/Privacy lead | Secrets, access, upload policy, incident response |
| QA/release lead | Smoke, regression, offline, permissions, release sign-off |
| Help desk lead | Первая линия для организаторов, судей, волонтеров и медиа |

## 3. Принцип подчинения и решений

В день события технический директор получает полномочия на технические действия, но не на спортивные решения.

`Event Director` принимает операционное решение.  
`Chief Judge` принимает судейское решение.  
`Technical Director` выбирает безопасный технический способ его реализовать.

Критические изменения требуют двух людей:

- deploy/rollback — TD + DevOps lead;
- scoring schema — chief judge + scorer;
- result publish — chief judge + scorer;
- security incident — TD + security lead;
- broadcast data switch — TD + режиссер трансляции.

## 4. Состояния технической готовности

`planned → configured → tested → ready → live → degraded → recovery → stable → closed`.

Система должна отдельно показывать:

- application health;
- API health;
- database health;
- network health;
- scoring health;
- notifications health;
- media ingest health;
- broadcast feed health;
- backup status;
- last sync.

Статус `green` не заменяет конкретные метрики и время последней проверки.

## 5. Тайминг работы технического директора

### D‑90…D‑60: технический паспорт

TD фиксирует:

- Event ID и окружения dev/staging/production;
- дату, часовой пояс и ожидаемую нагрузку;
- роли и критичные endpoints;
- scoring schema и protocol formats;
- число устройств;
- network plan;
- storage quota;
- media volume;
- backup/restore plan;
- emergency contacts;
- SLA восстановления;
- допустимый fallback.

На этом этапе нельзя оставлять единственную копию архитектуры в чате. Паспорт сохраняется в репозитории и документации.

### D‑60…D‑30: build и интеграции

Команда готовит:

- staging event;
- миграции БД;
- auth/OTP;
- permissions;
- roster/import;
- scoring endpoints;
- media upload;
- push;
- protocol export;
- live feed;
- audit log;
- feature flags для рискованных функций.

Каждая интеграция подключается через adapter. Секреты хранятся только в environment/secret manager.

### D‑30…D‑14: нагрузка и безопасность

Проверяются:

- пиковые входы участников;
- массовая отправка уведомлений;
- параллельный scoring;
- media uploads;
- повторный submit;
- reconnect;
- backup/restore;
- ограничение прав;
- file type/size;
- signed URLs;
- logs без PII;
- отказ основного API;
- отказ сети.

### D‑14…D‑7: onsite readiness

TD и leads проверяют оборудование на площадке:

- routers/AP;
- LTE/5G backup;
- scoring tablets;
- judge accounts;
- QR readers;
- batteries/chargers;
- display/TV;
- broadcast encoder;
- cameras/metadata;
- local clock;
- power backup;
- spare devices;
- printed emergency sheet.

### D‑2…D‑1: release freeze

Устанавливается freeze:

- запрещены несогласованные code changes;
- фиксируется release SHA/version;
- миграции проверены на staging;
- rollback command проверена;
- seed данных обезличен;
- smoke report подписан TD, QA и event director.

## 6. Рабочее место TD

Dashboard должен показывать:

- release version;
- deploy status;
- API latency/error rate;
- DB connections/locks;
- queue depth;
- push delivery;
- scoring submissions;
- sync conflicts;
- media queue/storage;
- broadcast feed;
- incident list;
- backup age;
- current/last sync.

Для каждого warning есть owner, SLA, severity и следующий шаг.

## 7. Операционный сценарий D0

### Открытие

1. TD проводит readiness call.
2. Проверяет release и конфигурацию Event ID.
3. Открывает live monitoring.
4. Подтверждает роли и доступ.
5. Проверяет первый check-in.
6. Проверяет первый judge submission в тестовой зоне.
7. Передает техническую готовность event director.

### Во время события

TD получает alerts, но не поток несрочных логов. Он видит impact:

- какая роль затронута;
- какие heats;
- сколько пользователей;
- есть ли потеря данных;
- есть ли fallback;
- кто owner;
- какой ETA.

### После события

- закрывает live mode;
- запускает backup;
- проверяет protocol snapshots;
- отзывает временный доступ;
- фиксирует incident report;
- передает post-event technical report.

## 8. Инцидент-менеджмент

### Severity

- **SEV‑0** — угроза безопасности или потери официальных данных;
- **SEV‑1** — scoring, check-in или live остановлены;
- **SEV‑2** — затронута часть пользователей, есть рабочий обход;
- **SEV‑3** — некритичная ошибка UI/поддержки.

### Процесс

`detect → classify → assign → contain → workaround → recover → verify → communicate → postmortem`.

Каждая запись содержит:

- время обнаружения;
- сервис;
- Event ID;
- impact;
- owner;
- действия;
- версии;
- affected roles;
- recovery time;
- root cause;
- follow-up.

### Примеры

**Не работает scoring:** остановить publish, сохранить локальные drafts, перейти на approved fallback, уведомить chief judge, не вводить данные в Excel как альтернативный SoT.

**Нет сети:** включить резервный канал, разрешить offline queue, показывать last sync, после reconnect провести conflict review.

**Поврежден deploy:** rollback на предыдущий versioned release, проверить health и протоколы, затем открыть incident.

**Утечка доступа:** отозвать токен, заблокировать пользователя, сохранить audit, подключить security lead и event director.

## 9. Backup и восстановление

Перед live:

- backup базы;
- backup конфигурации без секретов;
- snapshot scoring schema;
- сохранение roster/start list;
- проверка restore на staging;
- фиксация времени и версии.

После события:

- полный backup;
- protocol snapshots;
- media manifest;
- audit export;
- checksum;
- retention policy.

Целевой rollback для приложения — не более 15 минут, если инфраструктура это позволяет. Нельзя заявлять RTO/RPO без фактического теста.

## 10. Работа с релизами

Каждый live release имеет:

- commit SHA;
- migration version;
- config version;
- release notes;
- smoke result;
- rollback path;
- owner;
- approval.

Запрещены:

- ручные изменения production БД без migration;
- неизвестные hotfix на live;
- удаление логов до incident review;
- хранение `.env`, токенов и ключей в репозитории;
- фиктивные mobile artifacts.

## 11. Подчиненные и их ежедневный workflow

### Platform/API lead

Проверяет health, error budget, queue, permissions и API smoke. При изменении контракта обновляет API documentation и tests.

### Frontend/PWA lead

Проверяет 320/390 px, offline states, focus, aria labels, long text, retry и expired session. Не выпускает экран только для desktop, если его используют на площадке.

### Database/Data lead

Проверяет constraints, indexes, migrations, consistency, backup и отсутствие duplicate Athlete ID/run.

### DevOps/SRE

Проверяет deployment, logs, alerts, secrets, restart, rollback и health check.

### Scoring operator

Проверяет judge accounts, schema, queue, calculation, lock и protocol export. Не меняет sports rules без chief judge.

### Network operator

Проверяет основной и резервный канал, покрытие зон, power, latency и offline fallback.

### Broadcast engineer

Проверяет feed, lower third, result status, replay metadata и switch-over.

### Device support

Проверяет battery, app version, camera/QR permissions, storage, replacement devices и handover.

### Security lead

Проверяет least privilege, tokens, file uploads, signed links, audit и incident runbook.

### QA/release lead

Проводит smoke/regression/permission/offline/recovery tests и подписывает release report.

### Help desk lead

Ведет triage, SLA, escalation и FAQ, не запрашивая документы в незащищенных каналах.

## 12. AI Agents технического контура

| Agent | Разрешенная работа | Запрещено |
|---|---|---|
| Health Agent | Сводит метрики и предупреждения | Менять конфигурацию без approval |
| Release Agent | Готовит checklist и release notes | Deploy в production без TD |
| DB Safety Agent | Проверяет миграции, constraints и backup | Выполнять destructive migration |
| Incident Agent | Классифицирует и назначает owner | Закрывать SEV‑0/1 самостоятельно |
| Security Agent | Ищет секреты, опасные permissions и утечки | Отправлять данные во внешние сервисы |
| QA Agent | Генерирует smoke/regression cases | Помечать непроверенное как passed |
| Sync Agent | Анализирует queue/conflicts | Тихо перезаписывать данные |
| Cost/Capacity Agent | Подсвечивает storage/traffic risks | Масштабировать платные ресурсы без approval |

AI tool calls и approvals попадают в audit log. AI не получает полные пользовательские документы.

## 13. Definition of Done

Технический контур готов, когда:

- есть staging и versioned release;
- опубликованы health checks и runbook;
- все роли получают корректные permissions;
- scoring, check-in, notifications, media и broadcast прошли smoke;
- резервная сеть протестирована;
- offline queue и conflict resolution проверены;
- backup/restore реально выполнены;
- rollback проверен;
- logs не содержат PII и secrets;
- incident severity и escalation определены;
- временный доступ отзывается;
- protocol snapshot и audit сохраняются;
- команда имеет запасные устройства и контакты;
- одна реальная репетиция проходит без Excel как SoT.

## 14. Приоритет

### P0

1. Staging/production separation.
2. Health/monitoring/alerts.
3. Release freeze и rollback.
4. Backup/restore.
5. Scoring/check-in availability.
6. Offline queue.
7. RBAC и audit.

### P1

1. Broadcast feed monitoring.
2. Media ingest monitoring.
3. Incident dashboard.
4. Capacity and cost alerts.
5. Device fleet inventory.

### P2

1. Automatic anomaly triage.
2. Self-service diagnostics.
3. Predictive capacity planning.

## 15. Первый технический slice

`создать staging event → выдать роли → открыть check-in → отправить test score → создать protocol snapshot → выключить основной канал → выполнить offline actions → восстановить связь → синхронизировать → проверить health → выполнить rollback → восстановить previous release → закрыть event`.

Главный критерий: технический директор может доказать, что соревнование продолжится после ожидаемого сбоя и что официальные данные не будут потеряны или изменены незаметно.

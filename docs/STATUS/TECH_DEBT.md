# Tech Debt

**Дата:** 2026-08-24

| ID | Долг | Почему терпим | Когда закрывать |
|----|------|---------------|-----------------|
| TD-01 | DATA_MODEL.md описывал UUID; реализация Stage 1 — integer PK | Совместимость с SQLite seed; публичный API отдаёт int | Перед multi-instance / внешними интеграциями |
| TD-02 | Auth cookie vs pure JWT не зафиксирован до конца | Stage 1 Bearer JWT достаточен | До первого staging |
| TD-03 | shared-schema отстаёт от runtime models | SoT — `services/api` | каждый API-цикл (частично обновлён 0.3.0) |
| TD-04 | Нет frontend unit/e2e | Мало UI-критичных флоу; API покрыт pytest | При стабилизации UX |
| TD-05 | Offline sync только на бумаге | Не Stage 1 | Stage 3 |
| TD-06 | systemd/nginx примеры не в repo | Ops вручную | Перед первым server deploy |
| TD-07 | Риск путаницы с Download Center командами | Документы разведены | Держать ADR-0001 в правилах |
| TD-08 | Analytics sink TBD | События описаны; consent уже пишется | Stage 2 |
| TD-09 | Multi-role vs single primary role на EventMembership | Допустимы multi rows | Уточнить при CRUD memberships |
| TD-10 | Тексты LEGAL — рабочие редакции | Нет юр. экспертизы | Перед публичным prod |
| TD-11 | Seed-email `@participants.mywave.local` | Form Excel без личных почт | Когда появятся реальные email |
| TD-12 | Нет in-app notification log | SMTP заблокирован владельцем | следующий код-P0 |

Не маскировать долг под «готово в prod».

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
| TD-12 | In-app notification log | закрыт 2026-08-24: `/me/notifications` + `/notifications` | — |
| TD-13 | Нет загрузки документов события через API | закрыт 2026-08-24 upload + 0.5.8 access_class | — |
| TD-14 | Категории Казани «до 15/до 19» vs U14/U18 | нельзя выбрать молча | до start lists, ADR-0007 |
| TD-15 | Seed Excel пишет roster напрямую, минуя Import Center | совместимость local reseed | после стабилизации Import Center на staging |
| TD-16 | Нет Alembic; SQLite ALTER best-effort | Stage 1 sqlite | перед Postgres prod |
| TD-17 | Frontend unit/e2e и axe не гоняются в CI | нет harness | Stage 2 |

Не маскировать долг под «готово в prod».

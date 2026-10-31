# Tech Debt

**Дата:** 2026-10-27

| ID | Долг | Почему терпим | Когда закрывать |
|----|------|---------------|-----------------|
| TD-01 | DATA_MODEL.md описывал UUID; реализация Stage 1 — integer PK | Совместимость с SQLite seed; публичный API отдаёт int | Перед multi-instance / внешними интеграциями |
| TD-02 | Auth cookie vs pure JWT не зафиксирован до конца | Stage 1 Bearer JWT достаточен | До публичного prod |
| TD-03 | shared-schema отстаёт от runtime models | SoT — `services/api` | каждый API-цикл |
| TD-04 | Нет frontend unit/e2e | Мало UI-критичных флоу; API покрыт pytest | При стабилизации UX / после пилота |
| TD-05 | Offline sync только на бумаге | Не Stage 1 | Stage 3 |
| TD-06 | systemd/nginx примеры не в repo | Ops вручную | Перед первым server deploy |
| TD-07 | Риск путаницы с Download Center командами | Документы разведены | Держать ADR-0001 в правилах |
| TD-08 | Analytics sink TBD | События описаны; consent уже пишется | Stage 2 |
| TD-09 | Multi-role vs single primary role на EventMembership | Допустимы multi rows | Уточнить при CRUD memberships |
| TD-10 | Тексты LEGAL — рабочие редакции | Нет юр. экспертизы | Перед публичным prod |
| TD-11 | Seed-email `@participants.mywave.local` | Form Excel без личных почт | Когда появятся реальные email |
| TD-12 | In-app notification log | **закрыт** 2026-08-24 | — |
| TD-13 | Загрузка документов события через API | **закрыт** 0.5.0 | — |
| TD-14 | PDF protocol export отсутствует (есть HTML Print) | Достаточно для пилота | optional после dry-run |
| TD-15 | Deep-link из уведомлений в заявку | In-app journal есть | UX-polish после пилота |
| TD-16 | FieldMoment capture не в runtime на диске; `facts.moments` пустой | Template report работает без медиа | при подключении media/moments слоя |
| TD-17 | EventReport без UI-вкладки | API 0.5.8 достаточен для пилота curl | следующий UX-инкремент |
| TD-18 | OpenAI ключ опционален; без него local AI | ок для пилота | ключ owner при желании «облачного» стиля |
| TD-19 | STT voice notes ещё off | ENABLE_EVENT_REPORT_STT=0 | после media/moments |
| TD-20 | UI вкладка «Отчёт» / Excel | **закрыт 0.5.9** | — |

Не маскировать долг под «готово в prod».

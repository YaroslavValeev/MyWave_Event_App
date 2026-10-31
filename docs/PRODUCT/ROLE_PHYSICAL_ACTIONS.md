# Физические действия площадки ↔ роли ↔ приложение

Дата: 2026-10-27  
Канон в коде: `services/api/app/domain/role_physical_actions.py`  
API: `GET /api/v1/events/{id}/role-actions`  
Отчёт: лист Excel `RoleActions` + секция AI-хроники.

## Зачем

На воде люди делают **физические** шаги (стойка, понтон, лист оценок).  
В приложении те же шаги должны стать **цифровым фактом** и **передачей** следующей роли — без второго Excel как SoT.

## Матрица (кратко)

| Фаза | Физика | Роль | В App | Кому передать |
|------|--------|------|-------|---------------|
| prep | Документы на стойке | organizer | documents + checklist | judge |
| prep | Медсверка | organizer | checklist.medical | registrar/organizer |
| prep | Бейдж судье | organizer | role approve | judge |
| day | Check-in + bib | organizer | start_list → checked_in | judge |
| day | Вызов к понтону | support | → ready | judge |
| day | Старт на воду | judge | → on_water | judge |
| day | DNS / DNF | organizer/judge | dns / dnf | commentator / organizer |
| day | Оценки | judge | judge-scores / protocol photo | organizer |
| day | Утвердить место | organizer | results published | commentator |
| day | Кадр / заметка | commentator | moment / note | organizer |
| after | Протокол | organizer | official-protocol | federation_manager |
| after | Отчёт дня | organizer | event-report AI → publish + Excel | federation_manager |
| after | Архив | organizer | status completed | platform_admin |

Полный список кодов — в API / Excel / `ROLE_PHYSICAL_ACTIONS`.

## Правила handoff

1. Физическое действие без записи в App = дыра в отчёте.
2. Следующая роль не «угадывает» — смотрит статус в App (или уведомление).
3. Excel-выгрузка отчёта — **копия**, не место первичного ввода.
4. AI пишет хронику из фактов + этой матрицы; Publish — только человек.

## Связь с Казанью

Виртуальный прогон: [KAZAN_VIRTUAL_DRY_RUN.md](./KAZAN_VIRTUAL_DRY_RUN.md).  
На seed Казани пункты prep частично закрыты; day/after — виртуальная дописка до пилота.

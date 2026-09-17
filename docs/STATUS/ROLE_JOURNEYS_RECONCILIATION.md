# Сверка ролевых сценариев с кодом

**Дата:** 2026-09-17  
**Канон journeys:** [docs/PRODUCT/journeys/](../PRODUCT/journeys/ROLE_SCENARIOS_PACKAGE_README.md)  
**Код:** ветка `cursor/p0-import-center-athlete-link`, продукт **0.5.10** + FieldMoment **0.5.11 (не на staging)**

Целевые документы — спецификация, не описание текущего UI. Ниже — факт репозитория.

| Сценарий | Статус | В коде | Нет / позже |
|---|---|---|---|
| Участник | частично | OTP, профиль, Athlete ID, заявка, roster, документы, согласия, уведомления, **«Мой старт» на обзоре события** | платежи, waitlist, апелляция, личный альбом, deep link |
| Организатор | частично | паспорт, категории, импорт, officials, слоты, heats, checklist, **roster lock (0.5.9)**, **пульт Сейчас/Следующий/Внимание на обзоре** | maker-checker на всё, инциденты, полная state machine |
| Судья / скорер | частично | схема, judge sheet, aggregate → draft, verify; **publish только chief_judge (0.5.9)**; **текущий спортсмен на воде как цель оценки** | homologator, скрытие чужих оценок, апелляция |
| Фото/видео | частично | роль `media`/`commentator`/`support`, **FieldMoment** (камера PWA, ADR-0011) | EXIF, match Athlete ID, consent медиа, личный альбом, публикация наружу |
| Ведущий | частично | роль `commentator`, вкладка «Моменты» | rundown, delay wording, graphics feed |
| Волонтер | отсутствует | — | смены, зоны |
| TD | частично | health, staging runbook, backup | live ops dashboard |
| Капитан катера | отсутствует | статусы heat `ready`/`on_water` | boat cue UI |
| Режиссёр эфира | отсутствует | — | graphics feed |
| Казань SoT | частично | БД: состав, старты, draft места | часть баллов; draft до chief publish |

P0-срез брифа `create → registration → review → roster lock → heat → check-in → score → chief approval → official → protocol → archive`: **закрыт в API + pytest**; полевой dry-run на площадке — нет.

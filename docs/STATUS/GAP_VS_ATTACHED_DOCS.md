# Gap vs прикреплённые документы (2026-08-25)

Источники:
1. `MyWave_Экосистема_и_проекты_по_итогам_диалога_24-08-2026.docx`
2. `Production‑план и рабочий комплект для FVLS × MyWave Competition Hub.docx`

## Вердикт

**Нет — в Event App учтено не всё из этих документов.**  
Документы описывают всю экосистему MyWave и production-платформу Federation Hub на 22–30 недель.  
Этот репозиторий — **только** standalone Event App (SoT соревнования). Остальное — другие продукты / следующие этапы.

## Что из документов относится к Event App

| Требование | В docs / ROADMAP | В коде 0.5.2 |
|------------|------------------|--------------|
| Регистрация / роли / roster | да | да |
| Документы события | да | да |
| Checklist подготовки | да | да (событие) + **11 разделов площадки** на `/projects/checklist-org` |
| Heats / start lists / check-in | да | foundation |
| Results draft → published | да | foundation (ручной score/place) |
| Фото/PDF протокола | да (режим) | ProtocolCapture |
| Полевые моменты (камера) | да (срез 1) | FieldMoment PWA, ADR-0011; не альбом спортсмена |
| Rules / org (FVLS+IWWF) | ADR-0006 | catalog + EventRulesProfile |
| Structured scoring (DRIVE / T+I / EIC) | да | **done (0.5.3)** |
| Official protocol export | да | **partial (0.5.4)** JSON + HTML; PDF — позже |
| Read-only archive | да | **done (0.5.5)** |
| Athlete ID | да | **done (0.5.5)** |
| Media / photographer mode | этап 5 | **срез 1** FieldMoment; EXIF/альбом — нет |
| ParserNews / broadcast | этап 7–8 | **нет** (правильно позже) |
| Telegram / MAX / native / offline-first | Production-план Hub | **не Stage 1** (adapters позже) |
| SMTP + remote staging | owner | staging compose есть; host/SMTP — owner |

## Что намеренно НЕ делается в этом репо

- Ruza / Club Ops / Club Box
- Wake Challenge / методика Федерации
- AI Judge / AI Coach / Knowledge Base
- Sponsorship Platform
- Полный Production Hub с Mini Apps и 7–10 FTE планом

Принцип из экосистемы: **сначала один E2E цикл соревнования без Excel SoT**, потом расширения.

## Оценка

| Метрика | Аудит 24.08 | Сейчас |
|---------|-------------|--------|
| Путь до DoD v1 | ~32% | ~70% |
| Блокер продукта | git + start day | **pilot dry-run + live UX** |

## Следующий код (этот спринт)

1. Live board / DNS-DNF polish (дальше)
2. PDF export (optional)
3. Pilot dry-run

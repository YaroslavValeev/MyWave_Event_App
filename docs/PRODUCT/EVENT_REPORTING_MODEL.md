# Модель отчётности о событии

Дата: 2026-10-27  
Статус: канон (Stage 1.5 design + template-draft в API)  
ADR: [ADR-0012](../ARCHITECTURE/decisions/ADR-0012-event-reporting.md)  
Сценарий Казани: [KAZAN_VIRTUAL_DRY_RUN.md](./KAZAN_VIRTUAL_DRY_RUN.md)

## Проблема

После соревнования нужен понятный отчёт: кто стартовал, DNS/DNF, призёры, короткая хроника. Сейчас это часто второй Excel или «человек в штате на весь день». Хочется просто: факты уже в App → черновик сам → человек правит.

## Решение: Dual-track

**Live ops + Sparse moments + Template/AI draft + Human publish.**

| Слой | Когда | Кто | Что |
|------|-------|-----|-----|
| 1. Operational facts | Live | registrar, judge, organizer | check-in, DNS/DNF, scores, publish, checklist |
| 2. Field moments | Live, редко | commentator, media, support, chief | фото/видео + короткая заметка / голос→текст |
| 3. EventReport | После heat/дня | organizer / commentator / federation_manager | assemble draft → edit → publish |

Отдельный «штатный репортёр» **не обязателен**. AI/шаблон **не** судит и **не** публикует сам.

## Ответы на продуктовые вопросы

| Вопрос | Ответ |
|--------|-------|
| Заполнять Live? | Да — только операционные факты и редкие моменты. Не писать статью на понтоне. |
| После события? | Да — сборка и вычитка отчёта (15–30 мин). |
| Зачем человек? | Approve нарратива и выбор кадров; роли судьи/секретаря уже закрывают цифры. |
| Зачем AI / шаблон? | Склеить хронологию, места, DNS/DNF, handoff ролей. **AI включён** (local; OpenAI при ключе). Template — `use_llm=false`. |
| Excel? | Только **выгрузка** из App (`/event-report/excel`), не место ввода. |
| Голос | 15 сек → STT → текст к моменту (flag `ENABLE_EVENT_REPORT_STT`). Не live-радио. |
| Фото/Видео | Field moments (слой 2); в draft попадают только `approved`. |
| Чеклист | Prep (есть) + day-of коды: `day_starts_ready`, `day_medical_gate`, `day_protocol_filed` (расширение checklist). |
| Уведомления | In-app (есть) → email при SMTP → deep-link. Telegram/чат — адаптер, не SoT. |

## Анти-паттерны

- Второй Excel «для отчёта федерации» как SoT.
- Обязательный копирайтер на каждом заезде.
- AI publish без human approve.
- Дублирование results в отдельной «репортажной» таблице цифр.

## Сущность EventReport

| Поле | Описание |
|------|----------|
| event_id | → Event |
| status | `draft` \| `published` \| `void` |
| title | заголовок |
| body_markdown | текст хроники (редактируемый) |
| facts_json | снимок структурированных фактов на момент assemble |
| source | `template` \| `llm` (llm = AI local или OpenAI) |
| created_by / published_by / published_at | audit |

Один актуальный draft на событие; publish создаёт неизменяемый снимок в `facts_json` + body; void при пересборке.

## Поток

```text
Live: check-in / scores / moments
        ↓
POST /event-report/assemble   ← template из results + DNS/DNF + officials (+ approved moments)
        ↓
PATCH body / title            ← человек
        ↓
POST .../publish
        ↓
ParserNews / витрина (позже) читают published only
```

## Каналы уведомлений (приоритет)

1. In-app `/notifications` — уже SoT журнала.
2. Email — когда SMTP настроен.
3. Персональные виды: «старт скоро», «результат опубликован» (код позже).
4. Telegram / MAX — опциональный адаптер после стабилизации дня старта.

## Связь с DoD v1

Отчётность **не блокирует** минимальный DoD (подготовка→archive без Excel SoT), но закрывает боль «как рассказать о дне» без второго контура данных. Pilot dry-run ops → затем EventReport на тех же данных.

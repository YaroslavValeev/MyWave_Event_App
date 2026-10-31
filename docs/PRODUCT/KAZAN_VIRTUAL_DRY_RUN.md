# Виртуальный прогон — ЧР/ПР Казань 2026

Дата: 2026-10-27  
Продукт: MyWave Event App **0.5.7+**  
Событие seed: `chr-pr-kazan-2026`  
Связано: [EVENT_REPORTING_MODEL.md](./EVENT_REPORTING_MODEL.md), [HOW_TO_USE.md](../OPERATIONS/HOW_TO_USE.md), ADR-0012

Цель: прогнать DoD v1 **на бумаге/в голове** на реальных seed-данных Казани, явно отметив что уже в БД, что дописываем виртуально, и где ломаются негативные сценарии.

---

## 1. Что есть в seed (факт)

| Сущность | Оценка | Комментарий |
|----------|--------|-------------|
| Event | ✓ | `registration_open`, slug `chr-pr-kazan-2026` |
| Участники (Form) | ~97 | статус преимущественно `registered` |
| Категории | ~17 | Wakeboard boat / Wakesurf / Wakeskim |
| Медфлаг | ~51 ✓ | URL внутри БД; API отдаёт только bool |
| Официалы | 11 | протокол №32-КС; комментатор Валеев Я. |
| Документы | бюллетень, протокол КС, тренировки, IWWF rules | checklist `documents` auto-tick |
| Тренировочные слоты | ~162 (часть booked) | ≠ heats дня старта |
| Чеклист prep | 7 пунктов | medical — только вручную |
| Heats / start lists / runs | ✗ | не сидятся |
| Results / judge sheets | ✗ | |
| FieldMoment архив дня | ✗ / не в Stage 1 runtime | слой заложен моделью отчётности |
| EventReport | ✗ → появляется в коде после ADR-0012 | |
| SMTP / реальные email | ✗ | `*.mywave.local` + mail_outbox |

---

## 2. Виртуальная хронология

```text
T−7…T−1  Prep → роли → heats → start lists → Event live
День 0   Check-in → on_water → scoring → publish → moments
T+0…T+1  Official protocol → EventReport draft → approve → archive
```

### T−7…T−1 — Подготовка (позитив)

1. Организатор открывает Казань; чеклист: documents / categories / officials / registration / roster — частично зелёные от seed.
2. Manual tick `medical`: просмотр ~51 медфлагов; остальные «мед —» — решение допуска.
3. Создать User-memberships судьям из протокола №32-КС → `/admin/approvals` (Official ≠ автоматический login).
4. EventRulesProfile: FVLS + IWWF sanction, scoring mode по дисциплинам.
5. Heats по дисциплинам × категории → `POST .../start-list/fill`.
6. `PATCH` status → `live`.

**Виртуально дописываем:** heats H1…Hn, bib, судьи на heat, rules profile.

### День старта — Live ops

| Роль | Действие | Факт для отчёта |
|------|----------|-----------------|
| Registrar / organizer | check-in → ready → on_water | явка |
| Judge | sheet → aggregate → result draft | оценки |
| Organizer / chief | verified → published | места |
| Commentator / media | редкие фото/видео + короткая заметка | атмосфера / инциденты |
| Athlete | статус, слоты, уведомления | персональный контур |

### После дня

1. Official protocol JSON/HTML (уже в продукте).
2. `POST .../event-report/assemble` → template draft (без LLM).
3. Человек правит → `published`.
4. Event → `completed` → archive lock.

---

## 3. Позитивные сценарии (P)

| ID | Сценарий | Seed | Виртуальная дописка | Ожидаемый исход |
|----|----------|------|---------------------|-----------------|
| P1 | Happy path Wakesurf Open | roster категории | 1 heat, 8–12 атлетов, 3 judge sheets | published results + строки в EventReport |
| P2 | DNS до старта | участник в start list | статус `dns`, note no-show | в отчёте DNS, без места |
| P3 | DNF на воде | check-in прошёл | `dnf` + момент/заметка | DNF в хронике |
| P4 | Мед ✓ + publish-consent | has_medical_cert | grant consent в профиле | имя в публичном roster/results |
| P5 | Протокол КС в документах | document kind protocol | — | checklist documents ✓ |
| P6 | Комментатор ведёт пометки | Official commentator | 5–15 moments/notes за день | секция «моменты» в отчёте |
| P7 | Bulk fill start list | accepted/registered roster | fill API | start_lists checklist ✓ |
| P8 | Archive после publish | — | completed | мутации 409; report read-only |

---

## 4. Негативные / стресс (N)

| ID | Сценарий | Риск | Как закрывать | Пробел сейчас |
|----|----------|------|---------------|---------------|
| N1 | Нет SMTP | OTP/approve только outbox | owner: staging SMTP | host + App Password |
| N2 | Судья без membership | нет вкладки судейства | Доступы / approve | Official seed ≠ User role |
| N3 | Финал без медфлага | допуск «на честном слове» | checklist + будущий gate | нет жёсткого API gate |
| N4 | Протест места | спор рейтинга | void → новый draft; history есть | нет UX «протест» |
| N5 | Путаница bib / order | неверный старт | unique constraints | слабые UI-варнинги |
| N6 | Сеть на воде | потеря live input | ProtocolCapture фото листа | offline Stage 3 |
| N7 | Publish без verify | ошибка рейтинга | status machine | дисциплина процесса |
| N8 | Email `*.local` | спортсмен не видит письмо | in-app notifications | реальные email |
| N9 | «Судья при участниках» без ФИО | дыра в коллегии | назначить человека | placeholder Official |
| N10 | No-show тренировок | booked ≠ факт | не смешивать со start day | нет training→heat |
| N11 | Archive слишком рано | нельзя править | escape status→live | дисциплина |
| N12 | Медиа без модерации | PII / неудачный кадр | approve/withheld moments | процесс + UI |
| N13 | Два оркестратора отчёта | Excel + App | SoT только API | анти-паттерн |
| N14 | AI publish сам | ложный нарратив | human approve обязателен | ADR-0012 |

---

## 5. Матрица достаточности данных

| Цель | Seed хватает? | Что нужно |
|------|---------------|-----------|
| Демо подготовки / витрины | да | — |
| Полный DoD v1 в приложении | нет | heats, scores, publish, report |
| Боевой пилот на площадке | нет | SMTP, роли login, medical gate, fallback протокол |
| Отчёт федерации без Excel SoT | после EventReport | assemble + approve |

---

## 6. Чеклист ручного dry-run (когда будете на площадке / staging)

1. Reseed Казань → войти platform_admin.
2. Approve 1 judge + 1 commentator как User.
3. Rules profile + 1 heat + fill start list (5–10 человек достаточно для пилота).
4. Check-in двоих; одному DNS; одному полный run → scores → publish.
5. Protocol export HTML.
6. Assemble EventReport → править 5 мин → publish.
7. Completed → убедиться, что мутации закрыты.
8. Зафиксировать боли UX в TECH_DEBT / issue list.

Критерий успеха виртуального прогона: владелец понимает разрывы seed↔DoD и не путает «есть в Excel Казани» с «проведено в Event App».

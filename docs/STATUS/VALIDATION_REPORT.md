# Validation Report — 0.5.8 Import Center / Athlete ID

Дата: 2026-08-30  
Продукт: standalone MyWave Event App  
Цикл: AthleteProfile + Import Center + pending_claim (Казань-2026 staging, без PII в git)

## Проверки

| Проверка | Результат |
|----------|-----------|
| lint (ruff) | unavailable (не подключён в репо) |
| typecheck web (`tsc --noEmit`) | **passed** |
| unit/integration pytest | **65 passed** |
| import / claim / restricted docs | included in pytest |
| migrations | SQLite `create_all` + `_ensure_sqlite_columns` (Alembic нет) |
| web production build | не запускался в этом цикле |
| security (негативные permission) | participant 403 на import; medical-restricted 403 на file; takeover link 404; phone_taken 409 |
| accessibility | unavailable (axe/e2e не запускались) |
| smoke staging | pending владельца после deploy 0.5.8 |
| Docker build | not run this cycle |
| Production deploy | **not performed** |

Не отмечено passed то, что не запускалось.

## Парсер Казани-2026 (только агрегаты, без телефонов/ДР/меда)

Локальный разбор Desktop-файлов парсером `import_parse` (файлы **не** в git):

| Источник | kind | строк | уникальных ФИО | уникальных телефонов (count) | без медфлага |
|----------|------|------:|---------------:|-----------------------------:|-------------:|
| Предварительная регистрация (ответы) | form_answers | 100 | 90 | 86 | 48 |
| Регистрация по категориям | category_roster | 68 | 61 | 59 | 33 |

Дисциплины формы: Wakeboard (boat) 49, Wakeskim 27, Wakesurf 24.  
Дисциплины roster: Wakeboard (boat) 30, Wakesurf 18, Wakeskim 20.

После commit на staging числа профилей / pending accounts появятся в отчёте импорта UI (без PII). Пока БД staging пустая — commit не выполнялся.

## Что подтверждено тестами

- Повторная загрузка того же xlsx → тот же `ImportBatch`
- Повторный commit не плодит participants
- Pending account + OTP + confirm → `active` + Athlete ID
- Регистрация на занятый импортированный телефон → 409 `phone_taken`
- Confirm чужого `link_id` → 404
- Один телефон, два ФИО → два `AccountAthleteLink`
- Participant не видит medical-restricted документ

## Ограничения

- Реальные xlsx Казани загружает владелец на staging через `/admin/imports`.
- Категории бюллетеня vs IWWF — ADR-0007, decision required.
- Seed `scripts/seed_kazan_2026.py` по-прежнему пишет roster напрямую; для пилота использовать Import Center, не silent seed.

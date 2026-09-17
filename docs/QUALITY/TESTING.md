# Testing Strategy

**Дата:** 2026-09-16  

## 1. Пирамида

| Уровень | Где | Цель Stage 1 |
|---------|-----|--------------|
| Unit | `services/api/tests` | domain services, permissions |
| API integration | pytest + TestClient | health, auth, events, applications, consent |
| Web component | apps/web (vitest/jest TBD) | критичные UI куски |
| E2E | Playwright (Stage 2) | organizer → publish result |
| Manual smoke | SERVER_COMMANDS | health после деплоя |

## 2. Минимум на PR

- `ruff` / format (когда подключён) + pytest green для затронутого API.
- Нет секретов в диффе.
- Документы STATUS обновлены при изменении поведения.

## 3. Тестовые данные

- Фабрики UUID; не prod dumps.
- Отдельный SQLite in-memory / temp file.

## 4. Что не тестируем как «готовое мобильное»

- APK/IPA — отсутствуют, пока env не содержит реальный HTTPS.
- Архивный Flask Download Center не gate основного app CI. Runtime выдачи покрыт `tests/test_app_downloads.py`.

## 5. Критерий готовности Stage 1 testing

- `/health` test.
- Хотя бы один authz test (athlete не publish event).
- Consent: отказ регистрации без документов; маскировка roster.
- Документированный способ запуска: `pytest` из `services/api` (**110 passed** на 2026-09-17, цикл 0.5.11: FieldMoment + каталог выдачи + roster lock).

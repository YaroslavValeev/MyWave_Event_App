# Интеграции

**Дата:** 2026-09-16  

## 1. Правило

Интеграции — **адаптеры** вокруг API. Source of truth остаётся в MyWave Event App DB.

## 2. Матрица

| Система | Stage | Направление | Статус |
|---------|-------|-------------|--------|
| Browser / PWA | 1 | Client → API | В работе (scaffold) |
| Postgres | 1 optional / prod | API → DB | Documented |
| Redis | optional | cache/queue | Не обязателен Stage 1 |
| Site_MyWave Download Center | archive + API handoff | Site → Event App API | Архив Flask в `releases/`; runtime 0.5.10 — `/api/v1/app-downloads` |
| Telegram | 4 | Adapter ↔ API | Feature flag off |
| MAX | 4 | Adapter ↔ API | Feature flag off |
| Analytics sink | 2+ | API/Web → sink | События описаны; sink TBD |
| Object storage (S3/local) | 2 | Artifacts | TBD |

## 3. Feature flags (.env)

```text
ENABLE_TELEGRAM_ADAPTER=0
ENABLE_MAX_ADAPTER=0
ENABLE_AUDIT_LOG=1
```

## 4. Контракт адаптера (будущий)

- Auth: service account / webhook secret.
- Только вызовы `/api/v1/...`.
- Не пишет напрямую в БД.
- Не хранит копию PII дольше политики retention.

## 5. Download Center / выдача приложения

Архив Flask-карточки: `releases/download-center-2026-08-02/` — не команды деплоя Event App.  
Runtime с 0.5.10: API каталога + UI `/projects/checklist-org`. Сайт потребляет страницу или API (ADR-0009). Подключение файлов: `docs/OPERATIONS/APP_DOWNLOADS.md`.

## 6. Запреты

- Не делать Telegram primary UX Stage 1.
- Не синхронизировать Event SoT в сайт двусторонне без отдельного ADR.

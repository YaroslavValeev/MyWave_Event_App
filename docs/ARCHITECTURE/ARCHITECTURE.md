# Architecture — MyWave Event App (факт)

Дата: 2026-08-24

## Формула

Standalone продукт = `apps/web` (PWA) + `services/api` (FastAPI) + единая БД + `packages/shared-schema`.

Telegram/MAX — адаптеры (Этап 2).  
`releases/download-center-*` — архив выдачи сборок, не runtime.

## Компоненты Stage 1

```text
Browser / PWA
    │
    ▼
apps/web (Next.js)
    │ HTTP JSON
    ▼
services/api (FastAPI)
    │
    ▼
SQLite (local) / PostgreSQL (prod DATABASE_URL)
```

## Границы

| Можно | Нельзя |
|-------|--------|
| Развивать домен событий в API | Делать сайт MyWave ядром |
| Добавлять адаптеры каналов | Дублировать store в нескольких приложениях |
| Хранить архивы в releases/ | Смешивать archive patch с API кодом |

## Auth

JWT Bearer. Dev-login только в development/test.  
Регистрация: phone + email + обязательные согласия `terms_of_use` / `privacy_policy`.  
Критичные статусы дублируются в in-app `Notification`, пока SMTP не настроен.

# MyWave Event App — Web (Stage 1)

Standalone PWA shell: Next.js App Router + TypeScript + CSS Modules.

**Не** интегрируется во Flask Site_MyWave. Канал выдачи APK (`releases/download-center-*`) не трогаем.

## Стек

- Next.js 15 (App Router)
- TypeScript
- CSS Modules
- Шрифты: **Sora** + **IBM Plex Sans** (`next/font/google`)
- Тема: deep teal / night-ink / sand

## Страницы Stage 1

| Путь | Назначение |
|------|------------|
| `/` | Brand-first hero + CTA |
| `/login` | Dev-вход (email + роль) → JWT в localStorage |
| `/events` | Список событий с API |
| `/health` | Статус `GET /health` |

## Команды

```powershell
cd apps\web
copy .env.example .env.local
npm install
npm run dev
```

Сборка:

```powershell
cd apps\web
npm install
npm run build
npm start
```

Откройте http://127.0.0.1:3000

## Переменные

См. `.env.example`:

- `NEXT_PUBLIC_API_BASE_URL` — базовый URL API (по умолчанию `http://127.0.0.1:8000`)
- `NEXT_PUBLIC_APP_NAME` — имя приложения

API должен быть запущен отдельно (`services/api`, порт 8000).

## Контракты

- `GET /health`
- `POST /api/v1/auth/dev-login` — `{ email, role, display_name? }` → `{ access_token, user }`
- `GET /api/v1/events` — Bearer token → массив событий

Роли и статусы зеркалят `packages/shared-schema`.

## PWA

- `public/manifest.webmanifest`
- `public/icons/icon.svg`

Service Worker на Stage 1 не подключаем — только манифест.

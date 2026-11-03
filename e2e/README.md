# Playwright E2E — Champ App

## Запуск API-сценариев (SC01–SC09)

1. Поднять API в development (чтобы работал `dev-login`):

```powershell
cd services\api
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

2. В другом терминале:

```powershell
cd e2e
npm install
npx playwright install chromium
$env:E2E_API_BASE="http://127.0.0.1:8000"
npm run test:api
```

## UI smoke

```powershell
$env:E2E_WEB_BASE="http://127.0.0.1:3000"
npm run test:ui
```

## SC10 Xiaomi 14

Только ручной чек-лист: `docs/OPERATIONS/XIAOMI14_TEST_CHECKLIST.md`.

# MyWave Event App

Самостоятельная цифровая платформа соревнований для участников, организаторов, судей, комментаторов и администраторов.

**Продукт:** MyWave Event App  
**Альтернативное название (глоссарий):** FVLS × MyWave Competition Hub — не переименовывать без решения владельца.

## Архитектурный канон

- Ядро: **Web/PWA + API + единая БД**.
- Telegram / MAX / Site_MyWave / TGK_MyWave — **не** архитектурное ядро; при необходимости — внешние адаптеры.
- `releases/download-center-2026-08-02/` — **архивный** материал канала выдачи сборок (когда появятся), не само приложение.
- Мобильных сборок (APK/IPA) в репозитории **нет**.

## Быстрый старт (локально, Stage 1)

**Одна команда (Windows):**

```powershell
cd "F:\Проекты MyWave\NEW2026\App Champ\MyWave_Event_App"
npm run dev
```

Скрипт `scripts/dev.ps1` сам поднимет API и Web в двух окнах.

Ручной запуск (если нужно по отдельности):

```powershell
# API
cd services\api
$env:PYTHONPATH = (Get-Location).Path
$env:APP_ENV = "development"
C:\tmp\mw_event_api_venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8000

# Web (второй терминал)
cd apps\web
npm run dev -- --hostname 127.0.0.1 --port 3000
```

Docker Compose (опционально):

```bash
docker compose up --build
```

| Сервис | URL |
|--------|-----|
| API health | http://127.0.0.1:8000/health |
| OpenAPI | http://127.0.0.1:8000/docs |
| Web | http://127.0.0.1:3000 |

## Структура репозитория

```text
apps/web/                 # Next.js PWA (Stage 1)
services/api/             # FastAPI + домен событий/ролей
packages/shared-schema/   # общие контракты (по мере роста)
docs/                     # канонические документы
releases/                 # архивные релиз-пакеты (Download Center)
.cursor/rules/            # правила для AI-агентов
```

## Документация

**Как пользоваться (состав + сценарии):** [docs/OPERATIONS/HOW_TO_USE.md](docs/OPERATIONS/HOW_TO_USE.md)  
Команды владельца: [docs/OPERATIONS/OWNER_COMMANDS.md](docs/OPERATIONS/OWNER_COMMANDS.md)  
Индекс: [docs/CANONICAL_DOCS_INDEX.md](docs/CANONICAL_DOCS_INDEX.md)  
Статус: [docs/STATUS/CURRENT_STATE.md](docs/STATUS/CURRENT_STATE.md)  
Агенты: [AGENTS.md](AGENTS.md)

## Статус на 2026-08-24

Stage 1 **рабочий локально**: phone-auth, seed Казань из Form Excel (97 участников), заявки, approve ролей, профили, согласия/документы, табы карточки события. Pytest 29 passed. Production/SMTP — за владельцем. Мобильных сборок нет.

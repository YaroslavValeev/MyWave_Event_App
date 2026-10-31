# Команды: EventReport + AI + Excel (0.5.9)

Дата: 2026-10-27  
Секреты в команды не копировать. `OPENAI_API_KEY` только в `.env` на машине/сервере.

## 0) Env (обязательно для OpenAI)

В корневом `.env` (уже gitignore):

```env
ENABLE_EVENT_REPORT_LLM=1
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

Проверка без печати ключа (PowerShell, корень репо):

```powershell
cd "F:\Проекты MyWave\NEW2026\App Champ\MyWave_Event_App"
C:\tmp\mw_event_api_venv\Scripts\python.exe -c "import sys; sys.path.insert(0,'services/api'); from app.config import get_settings; get_settings.cache_clear(); s=get_settings(); print('llm', s.enable_event_report_llm, 'key', bool(s.openai_api_key), 'model', s.openai_model)"
```

Ожидание: `llm True key True model gpt-4o-mini`

## 1) Локальный запуск

Порт **8000** часто занят Docker Desktop — `npm run dev` сам уйдёт на **8010** и пропишет `apps/web/.env.local`.

```powershell
cd "F:\Проекты MyWave\NEW2026\App Champ\MyWave_Event_App"
npm run dev
```

UI: http://127.0.0.1:3000 → событие → вкладка **Отчёт**.

Полный виртуальный день на Казани (heat → DNS → result → AI report → Excel → publish):

```powershell
npm run dry-run:kazan
# или явно:
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\dry_run_kazan.ps1 -ApiBase http://127.0.0.1:8010
```

## 2) Smoke API (PowerShell)

```powershell
cd "F:\Проекты MyWave\NEW2026\App Champ\MyWave_Event_App"

# health
curl.exe http://127.0.0.1:8000/health

# token organizer (только development)
$login = curl.exe -s -X POST http://127.0.0.1:8000/api/v1/auth/dev-login -H "Content-Type: application/json" -d "{\"email\":\"organizer@example.com\",\"role\":\"organizer\"}"
$token = ($login | ConvertFrom-Json).access_token
# если ConvertFrom-Json ругается на UTF-8 BOM — возьмите access_token из ответа вручную

# EVENT_ID: для Казани после seed обычно 1
$EVENT_ID = 1

# AI assemble
curl.exe -s -X POST "http://127.0.0.1:8000/api/v1/events/$EVENT_ID/event-report/assemble" `
  -H "Authorization: Bearer $token" -H "Content-Type: application/json" -d "{\"use_llm\":true}"

# В JSON смотрите: "source":"llm", facts.ai.provider = "openai" | "local"

# Excel
curl.exe -L -o "$env:TEMP\event-$EVENT_ID-report.xlsx" `
  "http://127.0.0.1:8000/api/v1/events/$EVENT_ID/event-report/excel" `
  -H "Authorization: Bearer $token"

# Role handoffs
curl.exe -s "http://127.0.0.1:8000/api/v1/events/$EVENT_ID/role-actions?phase=day" `
  -H "Authorization: Bearer $token"

# Publish (после правки текста)
curl.exe -s -X POST "http://127.0.0.1:8000/api/v1/events/$EVENT_ID/event-report/publish" `
  -H "Authorization: Bearer $token" -H "Content-Type: application/json" -d "{}"
```

Скрипт-обёртка: `scripts/smoke_event_report.ps1`

## 3) Тесты

```powershell
cd "F:\Проекты MyWave\NEW2026\App Champ\MyWave_Event_App"
npm run test:api
```

## 4) Staging Docker (локально или на VPS)

```powershell
cd "F:\Проекты MyWave\NEW2026\App Champ\MyWave_Event_App"
Copy-Item .env.staging.example .env.staging -ErrorAction SilentlyContinue
# В .env.staging добавить:
# ENABLE_EVENT_REPORT_LLM=1
# OPENAI_API_KEY=sk-...
# OPENAI_MODEL=gpt-4o-mini
# SECRET_KEY=... (≥32)

docker compose -f docker-compose.staging.yml --env-file .env.staging up --build -d
curl.exe http://127.0.0.1:8001/health
```

## 5) Linux server (systemd / bare)

После `git pull` на сервере (см. также [SERVER_COMMANDS.md](./SERVER_COMMANDS.md)):

```bash
export APP_DIR="${APP_DIR:-/var/www/mywave-event-app}"
export APP_USER="${APP_USER:-mywave}"
cd "$APP_DIR"

# 1) Env на сервере (не в git)
grep -E '^(ENABLE_EVENT_REPORT_LLM|OPENAI_|SECRET_KEY)=' .env || echo "WARN: check .env"

# 2) Зависимости API (нужен openpyxl)
cd "$APP_DIR/services/api"
sudo -u "$APP_USER" bash -lc 'source .venv/bin/activate && pip install -r requirements.txt'

# 3) Web build
cd "$APP_DIR/apps/web"
sudo -u "$APP_USER" npm ci
sudo -u "$APP_USER" npm run build

# 4) Restart
sudo systemctl restart mywave-event-api
sudo systemctl restart mywave-event-web || true

# 5) Health
curl -fsS http://127.0.0.1:8000/health
curl -fsS http://127.0.0.1:8000/ready
```

Полный helper-deploy: блок в [SERVER_COMMANDS.md](./SERVER_COMMANDS.md).

## 6) Критерий «AI реально работает»

В ответе assemble:

```json
"source": "llm",
"facts": { "ai": { "provider": "openai" } }
```

Если `provider": "local"` — ключ не дошёл до процесса API (перезапуск) или OpenAI вернул ошибку (смотри логи API).

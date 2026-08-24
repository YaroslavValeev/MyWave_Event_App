# RUNBOOK — локальный запуск

## Windows (рекомендуется ASCII venv из-за кириллицы в пути)

```powershell
cd "F:\Проекты MyWave\NEW2026\App Champ\MyWave_Event_App"
Copy-Item .env.example .env
python -m venv C:\tmp\mw_event_api_venv
C:\tmp\mw_event_api_venv\Scripts\pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r services\api\requirements.txt
$env:PYTHONPATH="F:\Проекты MyWave\NEW2026\App Champ\MyWave_Event_App\services\api"
$env:APP_ENV="development"
C:\tmp\mw_event_api_venv\Scripts\uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Web:

```powershell
cd "F:\Проекты MyWave\NEW2026\App Champ\MyWave_Event_App\apps\web"
Copy-Item .env.example .env.local
npm install
npm run dev
```

## Linux server

См. `docs/OPERATIONS/SERVER_COMMANDS.md`.

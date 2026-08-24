# OWNER_COMMANDS — точные команды владельца

Корень репозитория (PowerShell):

```powershell
cd "F:\Проекты MyWave\NEW2026\App Champ\MyWave_Event_App"
```

## 1) Запуск локально (API + Web)

```powershell
npm run dev
```

Или раздельно:

```powershell
# API
cd "F:\Проекты MyWave\NEW2026\App Champ\MyWave_Event_App\services\api"
$env:PYTHONPATH = (Get-Location).Path
$env:APP_ENV = "development"
$env:SECRET_KEY = "local-dev-secret-change-me-32chars!!"
$env:DATABASE_URL = "sqlite:///./data/mywave_event.db"
$env:CORS_ORIGINS = "http://127.0.0.1:3000,http://localhost:3000"
C:\tmp\mw_event_api_venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8000 --reload

# Web (второй терминал)
cd "F:\Проекты MyWave\NEW2026\App Champ\MyWave_Event_App\apps\web"
npm run dev -- --hostname 127.0.0.1 --port 3000
```

Открыть: http://127.0.0.1:3000

## 2) Пересборка БД Казань (seed)

Рекомендуемый способ (сам остановит API, seed, поднимет API):

```powershell
cd "F:\Проекты MyWave\NEW2026\App Champ\MyWave_Event_App"
npm run reseed
```

Или вручную — **сначала** остановите процесс на порту 8000, иначе WinError 32:

```powershell
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue |
  ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }

cd "F:\Проекты MyWave\NEW2026\App Champ\MyWave_Event_App\services\api"
$env:PYTHONIOENCODING = "utf-8"
C:\tmp\mw_event_api_venv\Scripts\python.exe "..\..\scripts\seed_kazan_2026.py" --reset-db
```

## 3) Тесты API

```powershell
cd "F:\Проекты MyWave\NEW2026\App Champ\MyWave_Event_App\services\api"
C:\tmp\mw_event_api_venv\Scripts\python.exe -m pytest -q
```

## 4) SMTP на Gmail (реальные OTP + approve на y.valeev@gmail.com)

1. Google Account → Security → **App passwords** (нужна 2FA).
2. Создайте пароль приложения «MyWave Event App».
3. В корне проекта создайте/дополните `.env`:

```env
OWNER_APPROVAL_EMAIL=y.valeev@gmail.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USER=y.valeev@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx
SMTP_FROM=y.valeev@gmail.com
API_PUBLIC_URL=http://127.0.0.1:8000
PUBLIC_WEB_URL=http://127.0.0.1:3000
```

4. Перезапустите API. Письма начнут уходить через SMTP; копии всё равно пишутся в `data\mail_outbox\`.

Проверка outbox без SMTP:

```powershell
Get-ChildItem "F:\Проекты MyWave\NEW2026\App Champ\MyWave_Event_App\data\mail_outbox" | Sort-Object LastWriteTime -Descending | Select-Object -First 5
```

## 5) Быстрый smoke без UI

```powershell
# health
curl.exe http://127.0.0.1:8000/health

# регистрация участника
curl.exe -X POST http://127.0.0.1:8000/api/v1/auth/register -H "Content-Type: application/json" -d "{\"phone\":\"+79001110001\",\"email\":\"test.athlete@example.com\",\"display_name\":\"Тест Участник\",\"requested_role\":\"participant\"}"

# заявка судьи (нужен approve)
curl.exe -X POST http://127.0.0.1:8000/api/v1/auth/register -H "Content-Type: application/json" -d "{\"phone\":\"+79001110002\",\"email\":\"test.judge@example.com\",\"display_name\":\"Тест Судья\",\"requested_role\":\"judge\"}"

# OTP для уже существующего телефона из seed
curl.exe -X POST http://127.0.0.1:8000/api/v1/auth/phone/request-otp -H "Content-Type: application/json" -d "{\"phone\":\"+79647005403\"}"
```

Approve локально без почты:

- UI: войти как `organizer@example.com` через **dev-login** (только development) или как `y.valeev@gmail.com` после seed → http://127.0.0.1:3000/admin/approvals
- Либо открыть HTML-ссылку из последнего файла в `data\mail_outbox\`

Dev-login (только local):

```powershell
curl.exe -X POST http://127.0.0.1:8000/api/v1/auth/dev-login -H "Content-Type: application/json" -d "{\"email\":\"organizer@example.com\",\"role\":\"organizer\"}"
```

## 6) Что дальше по продукту

Локально уже сделано агентами: phone-auth, approvals UI, event applications, CI workflow.

Остаётся за владельцем:
1. SMTP (вы) → проверка OTP на реальную почту  
2. Staging deploy по `docs/OPERATIONS/SERVER_COMMANDS.md`
3. (опционально) привязать реальные email спортсменов вместо `p{phone}@participants.mywave.local`

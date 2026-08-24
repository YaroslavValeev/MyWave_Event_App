# MyWave Event App — API (Stage 1 P0)

Standalone FastAPI backend for MyWave Event App.
Not coupled to Site_MyWave, TGK, Flask download center, or Telegram/MAX as core.

## Stack

- Python 3.11+
- FastAPI + Pydantic v2
- SQLAlchemy 2
- SQLite locally (`DATABASE_URL`)

## Setup

```powershell
cd services/api
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
copy ..\..\.env.example ..\..\.env
```

Copy or edit `.env` at the repo root (or place `.env` next to this package).
See `.env.example` in this folder for the list of variables.

## Run

```powershell
cd services/api
.\.venv\Scripts\uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Health: `GET http://127.0.0.1:8000/health`

## Tests

```powershell
cd services/api
.\.venv\Scripts\pytest -q
```

## Stage 1 scope

- Health / ready
- Roles foundation
- Dev-login JWT (development only)
- Events CRUD (minimal)
- Audit log stub

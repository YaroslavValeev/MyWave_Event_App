# Server Commands — MyWave Event App (standalone)

**Дата:** 2026-10-27  
**Важно:** это деплой **самостоятельного** MyWave Event App (API + Web), **не** Flask Site Download Center.

Секреты в команды не подставлять. Значения брать из EnvironmentFile / секрет-хранилища сервера.

Для EventReport AI на сервере в `$APP_DIR/.env` должны быть:

```bash
ENABLE_EVENT_REPORT_LLM=1
OPENAI_API_KEY=...          # только на сервере
OPENAI_MODEL=gpt-4o-mini
```

После pull обязателен `pip install -r requirements.txt` (пакет `openpyxl` для Excel).  
Смок отчёта / dry-run: [EVENT_REPORT_COMMANDS.md](./EVENT_REPORT_COMMANDS.md).

## Если `sudo: unknown user mywave` / unit not found

Это **не** готовый prod-хост. Сначала диагностика (от root, **по одной команде**):

```bash
cd /var/www/mywave-event-app || pwd
whoami
id
ls -la
ls -la .env .env.staging 2>/dev/null || true
command -v docker; command -v docker-compose; docker compose version 2>/dev/null || true
systemctl list-units --type=service --all | grep -Ei 'mywave|uvicorn|next|nginx|docker' || true
ss -lntp | grep -E ':80|:443|:3000|:8000|:8001' || netstat -lntp | grep -E ':80|:443|:3000|:8000|:8001' || true
git remote -v; git status -sb; git rev-parse --short HEAD
```

Два рабочих пути ниже. **Не** копируйте блок `sudo -u mywave … systemctl restart mywave-event-*`, пока диагностика не покажет, что user и unit уже созданы.

### Путь A — Staging через Docker (рекомендуется для первого подъёма)

```bash
cd /var/www/mywave-event-app
git pull --ff-only origin main

cp -n .env.staging.example .env.staging
nano .env.staging
# Обязательно:
#   SECRET_KEY=... (>=32)
#   ENABLE_EVENT_REPORT_LLM=1
#   OPENAI_API_KEY=sk-...
#   NEXT_PUBLIC_API_BASE_URL=http://SERVER_IP:8001
#   API_PUBLIC_URL=http://SERVER_IP:8001
#   PUBLIC_WEB_URL=http://SERVER_IP:3001
#   CORS_ORIGINS=http://SERVER_IP:3001

docker compose -f docker-compose.staging.yml --env-file .env.staging up --build -d
docker compose -f docker-compose.staging.yml ps
curl -fsS http://127.0.0.1:8001/health
curl -fsSI http://127.0.0.1:3001/ | head -n 1
```

Порты снаружи: API **8001**, Web **3001**. Откройте их в firewall/security group.

### Путь B — Bare metal (создать user + systemd с нуля)

```bash
# 1) user
id mywave 2>/dev/null || useradd --system --create-home --shell /bin/bash mywave
chown -R mywave:mywave /var/www/mywave-event-app

# 2) code + deps (от mywave)
su - mywave -c 'cd /var/www/mywave-event-app && git pull --ff-only origin main'
su - mywave -c 'cd /var/www/mywave-event-app/services/api && python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt'
su - mywave -c 'cd /var/www/mywave-event-app/apps/web && npm ci && npm run build'

# 3) .env в корне репо (секреты только на сервере)
nano /var/www/mywave-event-app/.env

# 4) unit-файлы — создать вручную (в Stage 1 их нет в git), затем:
systemctl daemon-reload
systemctl enable --now mywave-event-api mywave-event-web
curl -fsS http://127.0.0.1:8000/health
```

Пример unit API (`/etc/systemd/system/mywave-event-api.service`):

```ini
[Unit]
Description=MyWave Event App API
After=network.target

[Service]
User=mywave
Group=mywave
WorkingDirectory=/var/www/mywave-event-app/services/api
EnvironmentFile=/var/www/mywave-event-app/.env
Environment=PYTHONPATH=/var/www/mywave-event-app/services/api
ExecStart=/var/www/mywave-event-app/services/api/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Web обычно через `next start` на 3000 за nginx — unit `mywave-event-web` или только nginx → `apps/web`.

Минимальный upgrade **только** когда user `mywave` и units уже есть:

```bash
cd /var/www/mywave-event-app
sudo -u mywave git pull --ff-only origin main
cd services/api && sudo -u mywave bash -lc 'source .venv/bin/activate && pip install -r requirements.txt'
cd ../../apps/web && sudo -u mywave npm ci && sudo -u mywave npm run build
sudo systemctl restart mywave-event-api mywave-event-web
curl -fsS http://127.0.0.1:8000/health
```

## Готовый блок (Linux)

Скопируйте на сервер и выполните по шагам. Перед первым запуском задайте реальные пути и имена unit-файлов.

```bash
#!/usr/bin/env bash
# MyWave Event App — server deploy helper (no secrets inline)
set -euo pipefail

# ---------------------------------------------------------------------------
# 1) Path / service vars
# ---------------------------------------------------------------------------
APP_DIR="${APP_DIR:-/var/www/mywave-event-app}"
APP_USER="${APP_USER:-mywave}"
SERVICE_NAME="${SERVICE_NAME:-mywave-event-api}"
WEB_SERVICE_NAME="${WEB_SERVICE_NAME:-mywave-event-web}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/mywave-event-app}"
GIT_REMOTE="${GIT_REMOTE:-origin}"
GIT_REF="${GIT_REF:-main}"
API_HEALTH_URL="${API_HEALTH_URL:-http://127.0.0.1:8000/health}"
API_READY_URL="${API_READY_URL:-http://127.0.0.1:8000/ready}"
WEB_HEALTH_URL="${WEB_HEALTH_URL:-http://127.0.0.1:3000/}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
PREV_SHA_FILE="${BACKUP_DIR}/prev_sha.txt"

echo "== MyWave Event App deploy ${STAMP} =="

# ---------------------------------------------------------------------------
# 2) State checks
# ---------------------------------------------------------------------------
command -v git >/dev/null
command -v curl >/dev/null
id "$APP_USER" >/dev/null
test -d "$APP_DIR"
test -f "$APP_DIR/.env" || { echo "ERROR: missing $APP_DIR/.env (create from .env.example, do not commit)"; exit 1; }
cd "$APP_DIR"
git rev-parse --is-inside-work-tree >/dev/null
echo "cwd=$(pwd) sha=$(git rev-parse --short HEAD) branch=$(git rev-parse --abbrev-ref HEAD)"

# ---------------------------------------------------------------------------
# 3) Backup
# ---------------------------------------------------------------------------
install -d -m 750 "$BACKUP_DIR"
git rev-parse HEAD > "${BACKUP_DIR}/sha-${STAMP}.txt"
cp -a "${BACKUP_DIR}/sha-${STAMP}.txt" "$PREV_SHA_FILE" 2>/dev/null || true
if [[ -f "$APP_DIR/data/mywave_event.db" ]]; then
  cp -a "$APP_DIR/data/mywave_event.db" "$BACKUP_DIR/mywave_event-${STAMP}.db"
  echo "sqlite backup ok"
fi
# Postgres (раскомментировать при DATABASE_URL=postgresql...):
# pg_dump "$DATABASE_URL" -Fc -f "$BACKUP_DIR/mywave_event-${STAMP}.dump"

# ---------------------------------------------------------------------------
# 4) Pull / apply
# ---------------------------------------------------------------------------
git fetch "$GIT_REMOTE" --tags
git checkout "$GIT_REF"
git pull --ff-only "$GIT_REMOTE" "$GIT_REF"
echo "new_sha=$(git rev-parse --short HEAD)"

# ---------------------------------------------------------------------------
# 5) Dependencies
# ---------------------------------------------------------------------------
# API
if [[ -d "$APP_DIR/services/api" ]]; then
  cd "$APP_DIR/services/api"
  if [[ ! -d .venv ]]; then
    sudo -u "$APP_USER" python3 -m venv .venv
  fi
  sudo -u "$APP_USER" bash -lc 'source .venv/bin/activate && pip install -r requirements.txt'
fi
# Web
if [[ -d "$APP_DIR/apps/web" && -f "$APP_DIR/apps/web/package.json" ]]; then
  cd "$APP_DIR/apps/web"
  sudo -u "$APP_USER" npm ci
fi

# ---------------------------------------------------------------------------
# 6) Migrations / bootstrap
# ---------------------------------------------------------------------------
cd "$APP_DIR/services/api"
# Предпочтительно Alembic, когда появится:
# sudo -u "$APP_USER" bash -lc 'source .venv/bin/activate && alembic upgrade head'
# Bootstrap fallback Stage 1 (если модуль есть):
sudo -u "$APP_USER" bash -lc 'source .venv/bin/activate && python -m app.bootstrap' \
  || echo "WARN: bootstrap skipped (module not ready yet)"

# ---------------------------------------------------------------------------
# 7) Build
# ---------------------------------------------------------------------------
if [[ -d "$APP_DIR/apps/web" && -f "$APP_DIR/apps/web/package.json" ]]; then
  cd "$APP_DIR/apps/web"
  sudo -u "$APP_USER" npm run build
fi

# ---------------------------------------------------------------------------
# 8) Restart
# ---------------------------------------------------------------------------
sudo systemctl restart "$SERVICE_NAME"
if systemctl list-unit-files | grep -q "^${WEB_SERVICE_NAME}"; then
  sudo systemctl restart "$WEB_SERVICE_NAME"
fi
sudo systemctl is-active --quiet "$SERVICE_NAME"

# ---------------------------------------------------------------------------
# 9) Health
# ---------------------------------------------------------------------------
sleep 2
curl -fsS "$API_HEALTH_URL" | tee /tmp/mwe-health.json
curl -fsS "$API_READY_URL" | tee /tmp/mwe-ready.json || echo "WARN: /ready not implemented yet"
curl -fsSI "$WEB_HEALTH_URL" | head -n 1 || echo "WARN: web health check failed"

# ---------------------------------------------------------------------------
# 10) API smoke
# ---------------------------------------------------------------------------
curl -fsS "$API_HEALTH_URL" | grep -qi 'ok\|healthy\|status' \
  && echo "API smoke: health OK" \
  || { echo "API smoke FAILED"; exit 1; }
# Расширять по мере появления публичных маршрутов:
# curl -fsS "http://127.0.0.1:8000/api/v1/events" | head -c 200

# ---------------------------------------------------------------------------
# 11) Logs
# ---------------------------------------------------------------------------
sudo journalctl -u "$SERVICE_NAME" -n 80 --no-pager || true
if systemctl list-unit-files | grep -q "^${WEB_SERVICE_NAME}"; then
  sudo journalctl -u "$WEB_SERVICE_NAME" -n 40 --no-pager || true
fi

# ---------------------------------------------------------------------------
# 12) Rollback (manual trigger)
# ---------------------------------------------------------------------------
# Использование при сбое ПОСЛЕ деплоя:
#   ROLLBACK_SHA=$(cat /var/backups/mywave-event-app/prev_sha.txt)
#   cd /var/www/mywave-event-app
#   git checkout "$ROLLBACK_SHA"
#   # восстановить DB при необходимости:
#   # cp -a /var/backups/mywave-event-app/mywave_event-YYYYMMDDTHHMMSSZ.db data/mywave_event.db
#   cd services/api && source .venv/bin/activate && pip install -r requirements.txt
#   # alembic / bootstrap as needed
#   sudo systemctl restart mywave-event-api
#   curl -fsS http://127.0.0.1:8000/health

echo "== deploy finished ${STAMP} =="
```

## Placeholders

| Variable | Example |
|----------|---------|
| `APP_DIR` | `/var/www/mywave-event-app` |
| `SERVICE_NAME` | `mywave-event-api` |
| `WEB_SERVICE_NAME` | `mywave-event-web` |
| `BACKUP_DIR` | `/var/backups/mywave-event-app` |
| `GIT_REF` | `main` или `v0.1.0-stage1` |
| `API_HEALTH_URL` | `http://127.0.0.1:8000/health` |

## Примечания

- Unit-файлы systemd и nginx config создаёт оператор отдельно; в репозитории Stage 1 их может ещё не быть.
- Пока код API/Web не полон, шаги 6–7 могут завершаться WARN — это ожидаемо до закрытия Stage 1 scaffold.
- Команды Download Center из архива `releases/` сюда **не** копировать.

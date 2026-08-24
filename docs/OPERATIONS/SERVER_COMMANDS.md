# Server Commands — MyWave Event App (standalone)

**Дата:** 2026-08-04  
**Важно:** это деплой **самостоятельного** MyWave Event App (API + Web), **не** Flask Site Download Center.

Секреты в команды не подставлять. Значения брать из EnvironmentFile / секрет-хранилища сервера.

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

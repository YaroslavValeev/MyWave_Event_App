# Staging

**Дата:** 2026-11-01  
**Статус:** remote Docker staging на VPS; публичный URL — через туннель или nginx (owner).

План дожима: [NEXT_HARDENING_PLAN.md](./NEXT_HARDENING_PLAN.md).

## Цель

Иметь среду, отличную от laptop-only, где:

- крутится тот же commit SHA, что и кандидат в релиз;
- `APP_ENV=staging`;
- SECRET_KEY не дефолтный (≥32 символов);
- есть `/health` (с полем `version`) и `/ready`;
- данные отделены от локальной dev-БД (`DATA_DIR=/data` в Docker).

## Быстрый подъём (Docker)

```bash
cd /var/www/mywave-event-app   # или корень репо
cp -n .env.staging.example .env.staging
nano .env.staging

# Рекомендуется:
bash scripts/staging_up.sh
# эквивалент без Ollama-сети:
# docker compose -f docker-compose.staging.yml --env-file .env.staging up --build -d
```

Проверки:

```bash
curl -fsS http://127.0.0.1:8001/health
curl -fsSI http://127.0.0.1:3001/ | head -n 1
```

Порты: API **8001**, Web **3001**.

### Ollama на том же хосте

```bash
# сеть должна существовать (пример: ai-team_default)
docker compose -f docker-compose.staging.yml -f docker-compose.staging.ollama.yml \
  --env-file .env.staging up -d --build
docker network connect ai-team_default mwe-staging-api 2>/dev/null || true
```

В `.env.staging`:

```env
OPENAI_BASE_URL=http://ai-team-ollama-1:11434/v1
OPENAI_API_KEY=ollama
OPENAI_MODEL=llama3.2:3b
OPENAI_TIMEOUT_SECONDS=300
ENABLE_EVENT_REPORT_LLM=1
```

Прямой `api.openai.com` с VPS в РФ часто даёт `403 unsupported_country_region_territory`.

## Доступ с ПК владельца (пока нет публичного DNS)

```powershell
ssh -N -L 127.0.0.1:18001:127.0.0.1:8001 -L 127.0.0.1:13001:127.0.0.1:3001 root@SERVER_IP
```

Браузер: http://127.0.0.1:13001 — API health: http://127.0.0.1:18001/health  

Если web собран с `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:18001`, API-вызовы из браузера идут в туннель.

## OTP без SMTP

Письма пишутся в `DATA_DIR/mail_outbox` (в Docker: `/data/mail_outbox`):

```bash
docker compose -f docker-compose.staging.yml exec api \
  sh -c 'ls -t /data/mail_outbox/*.txt | head -n 1 | xargs cat'
```

## SMTP (owner)

См. [OWNER_COMMANDS.md](./OWNER_COMMANDS.md) — блок Gmail. После заполнения `SMTP_*` в `.env.staging`:

```bash
docker compose -f docker-compose.staging.yml --env-file .env.staging up -d api
```

## Публичный URL (owner)

Пример vhost: [nginx-mwe-staging.example.conf](./nginx-mwe-staging.example.conf).  
Нужны: DNS A-запись, отдельный `server_name` (не ломать Site_MyWave), rebuild web с новыми `NEXT_PUBLIC_*`, UFW/панель firewall для 80/443.

## Диск

При `df -h /` ≥ 85%:

```bash
docker system df
docker system prune -af --volumes=false
# осторожно с --volumes — не удалять staging_api_data без бэкапа
```

## Требования к env

| Переменная | Минимум |
|------------|---------|
| `APP_ENV` | `staging` |
| `SECRET_KEY` | ≥32 символов |
| `DATABASE_URL` | отдельный файл/Postgres |
| `DATA_DIR` | в compose задано `/data` |
| `CORS_ORIGINS` / `PUBLIC_WEB_URL` / `API_PUBLIC_URL` | URL web/API как их видит браузер |
| `ENABLE_EVENT_REPORT_LLM` | `1` |
| `OPENAI_*` | Ollama/proxy или cloud |

## Что staging не делает

- Не заменяет production.
- Не хранит боевые PII без политики backup.
- Не является Source of Truth вместо Git remote.

# Staging

**Дата:** 2026-08-24  
**Статус:** runbook готов; host deploy — blocker владельца.

## Цель

Иметь среду, отличную от laptop-only, где:

- крутится тот же commit SHA, что и кандидат в релиз;
- `APP_ENV=staging`;
- SECRET_KEY не дефолтный (≥32 символов);
- есть `/health` и `/ready`;
- данные отделены от локальной dev-БД.

## Быстрый локальный staging (Docker)

Из корня репозитория:

```powershell
# 1) Скопировать env
Copy-Item .env.staging.example .env.staging
# Отредактировать SECRET_KEY и SMTP при необходимости

# 2) Поднять stack
docker compose -f docker-compose.staging.yml --env-file .env.staging up --build -d

# 3) Проверки
curl http://127.0.0.1:8001/health
curl http://127.0.0.1:3001/
```

Порты staging по умолчанию: API **8001**, Web **3001** (чтобы не конфликтовать с `npm run dev`).

## Требования к env

| Переменная | Минимум |
|------------|---------|
| `APP_ENV` | `staging` |
| `SECRET_KEY` | ≥32 символов, не из `.env.example` |
| `DATABASE_URL` | отдельный файл/Postgres, не dev sqlite |
| `CORS_ORIGINS` | URL staging web |
| `PUBLIC_WEB_URL` | URL staging web |
| `API_PUBLIC_URL` | URL staging API |

## Remote staging (VPS)

Owner:

1. Создать host (Docker-capable).
2. `git clone` remote-репозитория (не копировать папку с USB).
3. Checkout нужного tag (`v0.4.0` и далее).
4. Заполнить `.env.staging` на сервере (секреты только там).
5. `docker compose -f docker-compose.staging.yml --env-file .env.staging up -d --build`.
6. Записать в CURRENT_STATE: host, tag, дата, evidence `/health`.

### Обновление staging до 0.5.8 (Import Center)

После merge/tag: backup volume SQLite, `git fetch && git checkout <tag>`, `docker compose -f docker-compose.staging.yml --env-file .env.staging up -d --build`.  
Казанские xlsx **не** класть в git. Загрузка: войти организатором → `/admin/imports` → выбрать событие (создать draft/published если БД пустая) → загрузить файл с рабочей машины.  
Rollback: предыдущий tag + restore backup volume. Не `git reset --hard` на боевых данных.

## Что staging не делает

- Не заменяет production.
- Не хранит боевые PII без политики backup.
- Не является Source of Truth вместо Git remote.

## Критерий готовности Этапа 0.5

- [ ] `docker-compose.staging.yml` в репо
- [ ] `.env.staging.example` без секретов
- [ ] Документ STAGING.md (этот файл)
- [ ] Хотя бы один успешный подъём staging stack (локально или VPS)
- [ ] SHA/tag зафиксирован в CURRENT_STATE при первом remote staging

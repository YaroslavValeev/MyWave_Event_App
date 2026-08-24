# Backup & Restore

**Дата:** 2026-08-04  

## 1. Что бэкапить

| Объект | Stage 1 | Примечание |
|--------|---------|------------|
| SQLite file | обязательно | путь из `DATABASE_URL` / `data/*.db` |
| Postgres dump | если используется profile/prod | `pg_dump` |
| `.env` | отдельно, вне git | секреты; шифрованный store |
| uploads / artifacts | если есть `data/uploads` | |
| release tag / git SHA | обязательно | для rollback кода |

## 2. Backup (SQLite пример)

```bash
APP_DIR="${APP_DIR:-/var/www/mywave-event-app}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/mywave-event-app}"
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
install -d -m 750 "$BACKUP_DIR"
cp -a "$APP_DIR/data/mywave_event.db" "$BACKUP_DIR/mywave_event-${STAMP}.db"
# опционально:
# cp -a "$APP_DIR/.env" "$BACKUP_DIR/env-${STAMP}.env"   # хранить шифрованно
```

## 3. Backup (Postgres пример)

```bash
# PGPASSWORD и URL — из EnvironmentFile, не из shell history скрипта в wiki
pg_dump "$DATABASE_URL_FOR_DUMP" -Fc -f "$BACKUP_DIR/mywave_event-${STAMP}.dump"
```

## 4. Restore SQLite

1. Остановить API service.
2. Скопировать выбранный `.db` на место.
3. Проверить права пользователя сервиса.
4. Старт + `/health` + smoke.

## 5. Retention

- Daily: 7 копий.
- Weekly: 4 копии.
- Перед каждым релизом — обязательный pre-deploy backup (SERVER_COMMANDS).

## 6. Проверка целостности

- `sqlite3 file.db 'PRAGMA integrity_check;'`
- Или восстановление на staging и `/ready`.

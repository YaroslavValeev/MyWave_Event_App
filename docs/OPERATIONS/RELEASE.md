# Release Process

**Дата:** 2026-08-24  
**Версия дисциплины:** 0.4.0+

## 1. Типы релизов

| Тип | Содержимое |
|-----|------------|
| docs | только документы канона |
| app-semver | функциональные релизы `vX.Y.Z` |
| hotfix | срочный патч `vX.Y.Z+1` от последнего tag |
| archive-dist | материалы в `releases/` (Download Center) — **не** runtime |

## 2. Обязательная дисциплина (не опционально)

1. Единственная рабочая история — **remote Git** (GitHub). Локальный диск = рабочая копия, не SoT.
2. Каждый функциональный релиз = **git tag** `vMAJOR.MINOR.PATCH` + запись в `docs/STATUS/CHANGELOG.md`.
3. Версии синхронизированы:
   - root `package.json`
   - `apps/web/package.json`
   - `services/api/app/__init__.py` (`__version__`)
   - FastAPI `version=` в `main.py`
4. `docs/STATUS/CURRENT_STATE.md` обновлён в том же коммите, что и релиз.
5. CI зелёный на `main` перед tag (или tag только после зелёного push).
6. Rollback = checkout предыдущего tag + restore DB backup по `BACKUP_RESTORE.md`.

## 3. Чеклист перед релизом кода

1. CHANGELOG и CURRENT_STATE честные.
2. `pytest` + `npm run build` (локально или CI).
3. Нет секретов в диффе (`.env` не в commit).
4. API_CONTRACT согласован при ломающих изменениях.
5. Rollback SHA / previous tag известен.
6. Staging проверен на том же commit SHA (для `v0.5.0+`).

## 4. Команды релиза (PowerShell)

```powershell
# 1) Убедиться, что чисто и CI пройден
git status
git push origin main

# 2) Tag (после merge/commit на main)
git tag -a v0.4.0 -m "MyWave Event App 0.4.0"
git push origin v0.4.0

# 3) GitHub Release (опционально)
gh release create v0.4.0 --title "0.4.0" --notes-file docs/STATUS/CHANGELOG.md
```

## 5. Что нельзя

- Хранить единственную историю только локально.
- Ставить tag на неоттегированный набор файлов без CHANGELOG.
- Выпускать фиктивные APK/IPA.
- Делать production deploy без записи в CURRENT_STATE (дата, host, version, health).

## 6. Staging vs Production

| Среда | APP_ENV | Назначение |
|-------|---------|------------|
| development | `development` | локальная разработка |
| staging | `staging` | проверка релиза, seed или копия |
| production | `production` | боевое соревнование |

См. `docs/OPERATIONS/STAGING.md`.

## 7. Production

Production deploy считается выполненным **только** после записи в CURRENT_STATE (дата, host, version, health evidence). На 2026-08-24 production deploy **не** выполнялся.

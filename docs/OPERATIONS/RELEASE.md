# Release Process

**Дата:** 2026-08-04  

## 1. Типы релизов

| Тип | Содержимое |
|-----|------------|
| docs | только документы канона |
| stage1-scaffold | API/Web foundation |
| app-semver | функциональные релизы `vX.Y.Z` |
| archive-dist | материалы в `releases/` (Download Center и т.п.) — **не** runtime |

## 2. Чеклист перед релизом кода

1. CURRENT_STATE и CHANGELOG обновлены честно.
2. Тесты Stage уровня пройдены (TESTING.md).
3. Нет секретов в диффе.
4. OpenAPI / API_CONTRACT согласованы при ломающих изменениях.
5. Backup plan понятен.
6. Rollback SHA известен.

## 3. Версионирование

- Git tags: `v0.1.0-stage1`, затем semver.
- `APP_VERSION` / package version синхронизировать с tag.

## 4. Mobile builds

**Не выпускать** фиктивные APK/IPA. Когда появятся реальные артефакты — отдельный release notes + подключение URL в сайтный Download Center (внешний процесс).

## 5. Production

Production deploy считается выполненным **только** после записи в CURRENT_STATE (дата, host, version, health evidence). На 2026-08-04 production deploy **не** выполнялся.

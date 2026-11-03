# ADR-0014 — Доставка на Android (Xiaomi 14)

Дата: 2026-11-03  
Статус: accepted  
Связь: ADR-0002 (Web/PWA Stage 1), ROADMAP «каналы»

## Контекст

Нужна установка Champ App на Xiaomi 14. В репозитории нет Capacitor/Cordova/RN и нет APK.  
`apps/web` — Next.js 15 App Router без `output: 'export'` и без service worker (manifest-only PWA).

## Решение (минимальный риск)

### Фаза A — сейчас (без native wrapper)

1. Основной канал: **Web + installable PWA** (Chrome / системный браузер HyperOS).
2. Камера: `<input type="file" accept="image/*" capture="environment">` + выбор из галереи без `capture`.
3. Backend остаётся HTTPS API; клиент не становится SoT.

### Фаза B — Capacitor (после стабилизации публикаций + пилота)

1. Кандидат: Capacitor, обёртка существующего web-клиента.
2. Предпочтительный режим: **загрузка hosted URL** (staging/production), а не слепой `next export` — меньше поломок App Router.
3. Плагины: Camera, Filesystem/Preferences для черновиков; AndroidManifest permissions для камеры/медиа.
4. Debug APK только после успешного `cap sync` + Gradle assemble; SHA-256 артефакта фиксируется в STATUS.

### Запрещено

- Выдавать несуществующий / placeholder APK.
- Заявлять native Android готовность без артефакта и записи в `CURRENT_STATE.md`.

## Последствия

- Чек-лист Xiaomi 14 для Фазы A проверяет PWA/браузер; пункты APK остаются BLOCKED до Фазы B.
- Owner approval нужен для prod deploy и store-публикации (см. координацию агентов).

## Откат

Остаёмся на Web/PWA; каталог `android/` Capacitor не коммитить, пока сборка не воспроизводится.

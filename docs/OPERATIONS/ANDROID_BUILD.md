# Android Build — Champ App

Дата: 2026-11-04  
Статус: **BLOCKED на этой машине** — нет JDK / Android SDK (`java` не найден, `ANDROID_HOME` пуст).

## Стратегия (ADR-0014)

1. **Фаза A (сейчас):** PWA / Chrome на Xiaomi 14.
2. **Фаза B:** Capacitor wrapper вокруг hosted staging URL (не blind `next export`).

Скелет проекта: `apps/mobile/` (конфиг Capacitor). Сборка APK возможна только после установки:

- JDK 17+
- Android Studio / cmdline-tools
- `ANDROID_HOME` + platform-tools
- Node 20+

## Команды (когда SDK доступен)

```powershell
cd "F:\Проекты MyWave\NEW2026\App Champ\MyWave_Event_App\apps\mobile"
npm install
npx cap add android
# Указать server.url на HTTPS staging в capacitor.config.ts
npx cap sync android
npx cap open android
# Android Studio → Build → Build APK(s)
```

Или:

```powershell
cd android
.\gradlew.bat assembleDebug
```

Артефакт: `android/app/build/outputs/apk/debug/app-debug.apk`  
Зафиксировать SHA-256 в `CURRENT_STATE.md` только после реальной сборки.

## Запрещено

Выдавать placeholder / пустой файл как APK.

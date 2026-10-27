# Операции: подключение файлов скачивания MyWave Event App

Дата: 2026-09-16  
Статус: активный

Карточка выдачи живёт в Event App:

- UI: `/projects/checklist-org#mywave-event-app`
- UI: вкладка «Подготовка» карточки события
- API SoT: `GET /api/v1/app-downloads/manifest`

Нативные APK / AAB / TestFlight / ZIP исходников **не входят** в Git. Пока URL не задан, интерфейс честно показывает «Файл временно недоступен».

Документация по установке **входит** в репозиторий (`services/api/app/static/downloads/install-and-run.html`) и доступна как `/downloads/install-and-run.html`, пока `MYWAVE_EVENT_APP_DOCUMENTATION_URL` пустой или равен `{{documentation_url}}`.

## Переменные окружения

| Плейсхолдер | Env | Назначение |
|-------------|-----|------------|
| `{{android_download_url}}` | `MYWAVE_EVENT_APP_ANDROID_DOWNLOAD_URL` | HTTPS на APK/AAB или `/downloads/mywave-event.apk` |
| `{{ios_testflight_url}}` | `MYWAVE_EVENT_APP_IOS_TESTFLIGHT_URL` | HTTPS TestFlight (`https://testflight.apple.com/join/...`) |
| `{{source_archive_url}}` | `MYWAVE_EVENT_APP_SOURCE_ARCHIVE_URL` | HTTPS ZIP исходников |
| `{{documentation_url}}` | `MYWAVE_EVENT_APP_DOCUMENTATION_URL` | HTTPS PDF/HTML/ZIP инструкции |

Правила:

1. Для Android / iOS / source: пустое значение или литерал `{{...}}` → статус `unavailable`.
2. Для документации: пустой/`{{...}}` → bundled HTML `/downloads/install-and-run.html`.
3. Небезопасный URL (http, localhost, IP из частной сети, credentials в URL) → `error`.
4. Публичный HTTPS → `available`. URL **не** попадает в manifest/status.
5. Локальный путь только вида `/downloads/<файл>` относительно каталога `data/downloads/` API.

## Пример

```bash
# реальный объект в object storage
MYWAVE_EVENT_APP_ANDROID_DOWNLOAD_URL=https://downloads.example.org/mywave-event-0.5.10.apk

# или файл, положенный на сервер API
# скопировать в data/downloads/install-guide.pdf
MYWAVE_EVENT_APP_DOCUMENTATION_URL=/downloads/install-guide.pdf
```

После смены env перезапустить API. Проверка:

```bash
curl -sS http://127.0.0.1:8000/api/v1/app-downloads/manifest
curl -sS http://127.0.0.1:8000/api/v1/app-downloads/android/status
# handoff возвращает location только после явного POST
curl -sS -X POST http://127.0.0.1:8000/api/v1/app-downloads/android/handoff
```

Сайт MyWave не хранит эти URL у себя: см. [письмо разработчикам сайта](../INTEGRATIONS/SITE_MYWAVE_DOWNLOAD_HANDOFF.md).

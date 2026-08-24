# Runbook: подключение файлов MyWave Event app

## 1. Подготовить артефакты

Перед публикацией владелец сборки передаёт:

- подписанный Android APK или ссылку Google Play; AAB допустим для дистрибуции разработчикам, но не устанавливается напрямую;
- публичную/групповую TestFlight invite URL и подтверждённую совместимость iOS;
- очищенный ZIP исходников без `.env`, ключей подписи, provisioning profiles и credentials;
- пользовательскую и техническую документацию.

Для каждого файла зафиксировать: version, build number, SHA-256, byte size, дату сборки, минимальную OS и срок действия ссылки.

## 2. Разместить файлы

Предпочтительный вариант — S3/CDN с HTTPS, версионированными неизменяемыми именами и корректным `Content-Disposition`.

Допустимый локальный вариант — файл внутри `/static/` или отдельного Nginx location `/downloads/`. Не хранить мобильные бинарники в Git.

## 3. Обновить метаданные

В `configs/event_app_downloads.yaml` заменить значения `version`, `size`, `last_updated` и `requirements` для опубликованных артефактов. Непроверенные значения не заполнять.

## 4. Настроить окружение

В production `.env`:

```dotenv
MYWAVE_EVENT_APP_ANDROID_DOWNLOAD_URL=https://cdn.example/releases/mywave-event-1.0.0.apk
MYWAVE_EVENT_APP_IOS_TESTFLIGHT_URL=https://testflight.apple.com/join/REAL_CODE
MYWAVE_EVENT_APP_SOURCE_ARCHIVE_URL=https://cdn.example/releases/mywave-event-source-1.0.0.zip
MYWAVE_EVENT_APP_DOCUMENTATION_URL=https://cdn.example/docs/mywave-event-1.0.0.pdf
```

Не оставлять литералы `{{android_download_url}}`, `{{ios_testflight_url}}`, `{{source_archive_url}}`, `{{documentation_url}}`: они специально распознаются как отсутствующая конфигурация.

## 5. Локальная проверка

```bash
cd /path/to/TGK_MyWave_Site
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export ENABLE_GOOGLE_SERVICES=0
export DISABLE_TELEGRAM=1
pytest -q tests/test_event_app_downloads.py
python main.py
```

Открыть `http://127.0.0.1:5000/projects/checklist-org#mywave-event-app`.

## 6. Проверка production-конфигурации до релиза

```bash
curl -fsS http://127.0.0.1:5000/api/event-app-downloads/manifest | python3 -m json.tool
curl -fsS http://127.0.0.1:5000/api/event-app-downloads/android/status | python3 -m json.tool
curl -fsS -X POST http://127.0.0.1:5000/api/event-app-downloads/android/handoff | python3 -m json.tool
```

Проверить, что manifest и status не содержат URL, а handoff содержит ожидаемый URL только для выбранного артефакта.

## 7. Откат

Самый быстрый безопасный откат артефакта — очистить соответствующую переменную окружения и перезапустить приложение. UI перейдёт в «Файл временно недоступен», не ломая страницу чек-листа.

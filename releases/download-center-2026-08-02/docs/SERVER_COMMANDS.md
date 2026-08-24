# Точные команды для последующей установки на сервер

Команды рассчитаны на структуру проекта из production-шаблона: `/var/www/mywave`, systemd unit `mywave-site`, Nginx перед Gunicorn. Не запускать до локальной приёмки и подключения реальных URL.

## 1. Передать архив на сервер

С рабочей машины:

```bash
scp MyWave_Event_App_Download_Center_Release_Pack_2026-08-02.zip root@SERVER_IP:/tmp/
```

## 2. Распаковать и проверить patch

На сервере:

```bash
set -euo pipefail
APP_DIR=/var/www/mywave
PACK_ZIP=/tmp/MyWave_Event_App_Download_Center_Release_Pack_2026-08-02.zip
PACK_DIR=/tmp/mywave-event-app-release-2026-08-02
SERVICE_NAME=mywave-site

test -d "$APP_DIR/.git"
test -f "$PACK_ZIP"
mkdir -p "$PACK_DIR"
unzip -q "$PACK_ZIP" -d "$PACK_DIR"
cd "$PACK_DIR/MyWave_Event_App_Download_Center_Release_Pack_2026-08-02"
sha256sum -c CHECKSUMS.sha256

cd "$APP_DIR"
git status --short
git fetch origin main
git switch -c feature/mywave-event-app-download-center origin/main
git apply --check "$PACK_DIR/MyWave_Event_App_Download_Center_Release_Pack_2026-08-02/patch/mywave-event-app-download-center.patch"
```

Если `git status --short` показывает чужие изменения в затрагиваемых файлах, остановитесь и сначала сохраните/согласуйте их.

## 3. Применить и протестировать без публикации

```bash
set -euo pipefail
APP_DIR=/var/www/mywave
PACK_DIR=/tmp/mywave-event-app-release-2026-08-02/MyWave_Event_App_Download_Center_Release_Pack_2026-08-02

cd "$APP_DIR"
git apply "$PACK_DIR/patch/mywave-event-app-download-center.patch"
source .venv/bin/activate
python -m pip install -r requirements.txt
export SECRET_KEY=test-secret-key-for-predeploy-only
export FLASK_CONFIG=testing
export ENABLE_GOOGLE_SERVICES=0
export DISABLE_TELEGRAM=1
pytest -q tests/test_event_app_downloads.py
python -m compileall -q app
gunicorn --check-config main:app
unset SECRET_KEY FLASK_CONFIG ENABLE_GOOGLE_SERVICES DISABLE_TELEGRAM
```

## 4. Подключить реальные release URL

Отредактировать `/var/www/mywave/.env` и заменить значения на фактические HTTPS URL:

```dotenv
MYWAVE_EVENT_APP_ANDROID_DOWNLOAD_URL={{android_download_url}}
MYWAVE_EVENT_APP_IOS_TESTFLIGHT_URL={{ios_testflight_url}}
MYWAVE_EVENT_APP_SOURCE_ARCHIVE_URL={{source_archive_url}}
MYWAVE_EVENT_APP_DOCUMENTATION_URL={{documentation_url}}
```

Литералы `{{...}}` оставляют файл недоступным и безопасны до получения реальных ссылок.

## 5. Перезапустить и проверить

```bash
set -euo pipefail
sudo systemctl restart mywave-site
sudo systemctl is-active --quiet mywave-site
curl -fsS http://127.0.0.1:5000/health
curl -fsS http://127.0.0.1:5000/api/event-app-downloads/manifest | python3 -m json.tool
curl -fsS http://127.0.0.1:5000/api/event-app-downloads/android/status | python3 -m json.tool
curl -fsS https://mywavewake.ru/projects/checklist-org >/dev/null
sudo journalctl -u mywave-site -n 100 --no-pager
```

## 6. Зафиксировать после приёмки

```bash
cd /var/www/mywave
git add .env.example .env.sample app/routes/wake_industry.py app/services/event_app_downloads.py configs/event_app_downloads.yaml docs static/css/event_app_downloads.css static/js/event_app_downloads.js templates/wake_industry tests/test_event_app_downloads.py
git commit -m "feat(projects): add MyWave Event app download center"
```

`.env` не добавлять в Git.

## 7. Безопасный откат patch до commit

```bash
set -euo pipefail
APP_DIR=/var/www/mywave
PACK_DIR=/tmp/mywave-event-app-release-2026-08-02/MyWave_Event_App_Download_Center_Release_Pack_2026-08-02

cd "$APP_DIR"
git apply -R --check "$PACK_DIR/patch/mywave-event-app-download-center.patch"
git apply -R "$PACK_DIR/patch/mywave-event-app-download-center.patch"
sudo systemctl restart mywave-site
sudo systemctl is-active --quiet mywave-site
```

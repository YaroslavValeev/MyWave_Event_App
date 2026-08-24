# MyWave Event app — готовый релизный комплект Download Center

Этот комплект предназначен для локальной проверки и последующего внедрения блока скачивания в существующий сайт MyWave. Он подготовлен относительно актуального `origin/main` на дату 2026-08-02.

## Что можно запустить сразу

- карточку приложения в `/projects/checklist-org#mywave-event-app`;
- четыре канала: Android, iOS/TestFlight, исходный код, документация;
- API manifest/status/handoff;
- все состояния интерфейса и повторную попытку;
- аналитику и доступную клавиатурную навигацию;
- тесты без реальных release URL.

## Что нельзя считать мобильной сборкой

ZIP релизного комплекта — это готовая интеграция выдачи файлов для сайта, а не APK/IPA. Реальные мобильные исходники и подписанные сборки не были предоставлены. Их нельзя корректно восстановить по продуктовым документам, поэтому фиктивные бинарники не создавались.

## Структура ZIP

- `README_RU.md` — этот документ;
- `source-files/` — полный код изменённых и новых файлов с путями репозитория;
- `patch/mywave-event-app-download-center.patch` — единый patch;
- `docs/` — PRD, Technical Design, Runbook, Implementation Report и манифест артефактов;
- `test-results/VALIDATION_REPORT.md` — результаты локальных проверок;
- `release/RELEASE_MANIFEST.json` — машинный манифест;
- `CHECKSUMS.sha256` — контрольные суммы содержимого.

## Применение patch

```bash
cd /path/to/TGK_MyWave_Site
git fetch origin
git switch -c feature/mywave-event-app-download-center origin/main
git apply --check /path/to/mywave-event-app-download-center.patch
git apply /path/to/mywave-event-app-download-center.patch
```

Затем выполните локальную проверку из runbook. На сервер изменения не отправляются автоматически.

## Подключение реальных файлов

1. Разместите проверенные артефакты на HTTPS CDN/S3 либо в контролируемом локальном `/downloads/`.
2. Обновите version, size, last_updated и requirements в `configs/event_app_downloads.yaml`.
3. Заполните четыре `MYWAVE_EVENT_APP_*_URL` в server `.env`.
4. Перезапустите приложение и выполните HTTP/manual smoke-test.

Точные переменные и команды приведены в `docs/MYWAVE_EVENT_APP_DOWNLOAD_CENTER_RUNBOOK.md`.

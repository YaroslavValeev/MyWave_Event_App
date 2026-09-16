# ADR-0009 — Каталог выдачи MyWave Event App

Дата: 2026-09-16  
Статус: accepted  
Владелец: MyWave Event App

## Контекст

Организатору нужна точка выдачи готового решения. Исторический Flask Download Center живёт в архиве `releases/download-center-2026-08-02/` и относится к сайту, не к runtime этого приложения. Нативных APK/IPA в репозитории нет.

## Решение

1. Source of truth доступности артефактов — API Event App (`/api/v1/app-downloads/*`).
2. URL файлов хранятся только в env: `MYWAVE_EVENT_APP_*_URL`. Плейсхолдеры `{{android_download_url}}` и аналоги означают «не подключено».
3. Публичный manifest/status не содержат target URL. Handoff отдаёт `location` только после явного POST.
4. UI карточки — в Event App: `/projects/checklist-org` и вкладка подготовки события.
5. Сайт MyWave потребляет страницу или API, но не хранит параллельный каталог ссылок.
6. Сервер не выполняет GET/HEAD к target URL (нет SSRF).

## Последствия

- Пока файлы не подключены, UI честно показывает недоступность.
- Сайту нужен CORS origin либо iframe/ссылка на Event App.
- Появление APK/TestFlight — операция конфигурации, не релиз бинарников в Git.

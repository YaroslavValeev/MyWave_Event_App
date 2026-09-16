# Письмо разработчикам сайта Site_MyWave

Дата: 2026-09-16  
От: команда MyWave Event App  
Кому: разработчики сайта (раздел «Проекты» → «Чек-лист организатора»)  
Тема: совместная выдача готового решения MyWave Event App

---

Коллеги,

в Event App появился **канонический центр выдачи** приложения. Это не второй Download Center во Flask и не фиктивные APK. Source of truth — API этого репозитория. Сайт остаётся витриной и точкой входа для организаторов.

## Что уже сделано в Event App

- Страница: `/projects/checklist-org#mywave-event-app`
- Тот же блок на вкладке «Подготовка» карточки события
- Публичный манифест без URL файлов
- Handoff: ссылка выдаётся только после подтверждения пользователем
- Состояния: загрузка / доступен / временно недоступен / ошибка / успешный старт
- Аналитика: `mywave_event_app_card_viewed`, `platform_selected`, `download_clicked`, `download_succeeded`, `download_failed`

Сейчас нативных сборок **нет**. Пока в окружении стоят плейсхолдеры `{{android_download_url}}`, `{{ios_testflight_url}}`, `{{source_archive_url}}`, `{{documentation_url}}`, карточка показывает «файл временно недоступен». Это ожидаемо и правильно.

## Как работать вместе

Есть два безопасных варианта. Выберите один, не дублируйте URL в коде сайта.

### Вариант A (рекомендуем на ближайший спринт)

На странице `https://<сайт>/projects/checklist-org` вставьте блок «MyWave Event App»:

1. Заголовок и якорный `id="mywave-event-app"`.
2. Кнопка/карточка «Открыть готовое решение» → абсолютный URL Event App:
   - staging: `http://62.113.42.227:3001/projects/checklist-org#mywave-event-app`
   - production: публичный URL Event App, когда он появится.
3. Не копируйте Flask-патч из архива `releases/download-center-2026-08-02/` как runtime сайта.

Так сайт не хранит ссылки на APK и не расходится с фактическим статусом файлов.

### Вариант B (встроить карточку в вёрстку сайта)

Сайт вызывает API Event App (нужно добавить origin сайта в `CORS_ORIGINS` Event App):

| Метод | Путь | Назначение |
|-------|------|------------|
| GET | `/api/v1/app-downloads/manifest` | метаданные без URL |
| GET | `/api/v1/app-downloads/{android\|ios\|source\|documentation}/status` | повторная проверка |
| POST | `/api/v1/app-downloads/{id}/handoff` | получить `location` после подтверждения |
| POST | `/api/v1/analytics/events` | продуктовые события |

Ограничения:

- Не печатать `location` в HTML до подтверждения.
- Не проксировать handoff своим бэкендом к произвольным URL (SSRF).
- Формат ошибки Event App: `{ "error": { "code": "...", "message": "..." } }`.
- Handoff ограничен: 20 запросов с IP в минуту.
- Manifest/status отдают `Cache-Control: no-store`.

UI сайта должен сохранить визуальный стиль MyWave и русские подписи. Референс: `apps/web/src/components/AppDownloadCard.tsx`.

## Что сайт не делает

- Не кладёт APK/IPA в Git сайта.
- Не показывает «скачать», если status ≠ `available`.
- Не использует литералы `{{android_download_url}}` как href.
- Не считает архивный Flask Download Center каноном.

## План работ сайта (оценка)

1. Согласовать вариант A или B и origin Event App для CORS.
2. Добавить блок в `/projects/checklist-org` с якорем `#mywave-event-app`.
3. Проверить клавиатуру, `aria` и мобильную вёрстку 320–860 px.
4. Совместный smoke: недоступный файл, затем один реальный HTTPS (когда появится).
5. Не деплоить выдачу, пока Event App API не отвечает 200 на `/api/v1/app-downloads/manifest`.

## Контакты по контракту

Документы в репозитории Event App:

- `docs/OPERATIONS/APP_DOWNLOADS.md` — как подключать файлы
- `docs/API/API_CONTRACT.md` — эндпоинты
- `docs/API/ANALYTICS_EVENTS.md` — события
- `docs/ARCHITECTURE/decisions/ADR-0009-app-download-catalog.md` — границы

С уважением,  
команда MyWave Event App

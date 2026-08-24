# Technical Design: MyWave Event app Download Center

## Архитектура

Решение расширяет существующий Flask-монолит и шаблон чек-листа. Отдельное приложение, новый router или параллельная дизайн-система не создаются.

```text
configs/event_app_downloads.yaml
        │ metadata + env names
        ▼
app/services/event_app_downloads.py
        │ safe public model / validated handoff
        ├── GET /api/event-app-downloads/manifest
        ├── GET /api/event-app-downloads/<id>/status
        └── POST /api/event-app-downloads/<id>/handoff
                         │
                         ▼
template partial + event_app_downloads.js
```

## Компоненты

### Конфигурация

`configs/event_app_downloads.yaml` содержит только отображаемые метаданные и имена переменных окружения. Секреты и реальные release URL в Git не сохраняются.

### Сервис

`app/services/event_app_downloads.py`:

- читает YAML;
- формирует публичный manifest без URL и имён env;
- вычисляет `available`, `unavailable`, `error`;
- разрешает только HTTPS, `/static/` и `/downloads/`;
- блокирует credentials в URL, localhost, `.local`, непубличные literal IP и path traversal;
- возвращает target только в handoff после явного подтверждения.

### API

- Manifest отдаёт метаданные всех вариантов.
- Status повторно проверяет конкретный вариант.
- Handoff повторно валидирует target, имеет rate limit `20 per minute`, `no-store`, `nosniff` и `same-origin` referrer policy.
- Handoff освобождён от CSRF, поскольку не изменяет состояние и дополнительно ограничен по частоте. Он не выполняет серверный запрос к целевому URL.

### Клиент

`static/js/event_app_downloads.js` не зависит от фреймворка. Он управляет вкладками, состояниями, подтверждением, live-region, аналитикой и выдачей ссылки. Серверный partial остаётся содержательным до выполнения JavaScript.

### Стили

`static/css/event_app_downloads.css` использует текущие `--mw-*` токены и изолированный BEM namespace. Breakpoints: 860 px и 560 px.

## Модель безопасности

1. URL хранится только в окружении сервера.
2. Public manifest/status не содержат target.
3. Handoff возвращает target только после пользовательского действия.
4. Сервер не делает HEAD/GET к target, что исключает SSRF и зависимость страницы от внешнего хранилища.
5. Клиент не исполняет HTML из API; все значения вставляются через `textContent`.
6. При любой неполной или подозрительной конфигурации выдача закрывается.

## Известная граница

Состояние `available` подтверждает корректно настроенный target, но не существование удалённого объекта в конкретную секунду. Проверка фактической доступности должна выполняться CI/CD или мониторингом хранилища. Полное завершение браузерной загрузки для cross-origin URL не наблюдаемо; аналитика фиксирует успешный handoff.

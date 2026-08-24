# Validation Report: MyWave Event app Download Center

Дата проверки: 2026-08-02

База: `a08a468b58b29db7aebde916d13620a6b753cbc9`

Ветка: `agent/mywave-event-app-release-pack`

## Автоматические проверки

| Проверка | Результат |
|---|---|
| Black для изменённых Python-файлов | PASS |
| isort `--profile black` | PASS |
| flake8 `--max-line-length=100` | PASS |
| Python `compileall app` | PASS |
| Node `--check` для Download Center JS | PASS |
| YAML parse | PASS |
| Jinja parse/render | PASS |
| CSS balance/syntax smoke | PASS |
| `pip check` | PASS, broken requirements: 0 |
| Gunicorn `--check-config main:app` | PASS |
| Feature + related regression tests | 35 passed, 1 skipped |

Тестовый набор:

```text
tests/test_event_app_downloads.py
tests/integration/test_projects_display.py
tests/integration/test_analytics_api.py
tests/unit/test_booking_phase1.py
```

## HTTP smoke-test

Gunicorn: 1 eventlet worker, `127.0.0.1:5055`, testing config.

- `GET /projects/checklist-org` → 200, 142124 bytes;
- HTML содержит `#mywave-event-app`, `role=tablist`, readiness и JS bundle;
- manifest содержит 4 формата и не содержит `location`;
- тестовая документация `/static/css/branding.css` → `available`;
- handoff документации возвращает только ожидаемый локальный target;
- Android без target → 503 `artifact_unavailable`.

## Полная коллекция репозитория

`pytest --collect-only -q` обнаруживает 7 существующих ошибок, не относящихся к этому изменению:

1. одинаковое имя `test_booking_flow.py` в e2e/integration/ui вызывает import mismatch;
2. синтаксическая ошибка в `tests/playwright_booking_test.py:95`;
3. `test_ai_concierge_endpoint.py` вызывает `create_default_gateway()` без обязательного `app`;
4. три AI-теста импортируют отсутствующие `CoreAIGateway`/`ToolDefinition`.

Эти файлы не изменялись. Целевая и связанная выборка проходит полностью, кроме одного штатного skip аналитики.

## Ограничения стенда

- В `package.json` отсутствуют scripts `build` и `typecheck`; выполнить их невозможно.
- Docker CLI на стенде отсутствует; вместо Docker build выполнены compile, Gunicorn config и реальный HTTP smoke-test.
- Chromium не установлен. Попытка установить Playwright browser остановлена сетевым шлюзом, поэтому новый browser screenshot/axe-run для этой пересборки не создан.
- Responsive и accessibility покрыты структурой HTML/CSS, keyboard-кодом и статическими/route-тестами; окончательная ручная проверка на реальных устройствах остаётся обязательной.

## Чек-лист ручной проверки

- [ ] Desktop: 1440×900, карточка без горизонтального overflow.
- [ ] Tablet: 768×1024, две колонки выбора складываются корректно.
- [ ] Mobile: 390×844 и 320×568, все кнопки доступны и не обрезаны.
- [ ] Tab проходит по четырём форматам и кнопкам.
- [ ] Стрелки/Home/End переключают вкладки с корректным `aria-selected`.
- [ ] Модальное окно удерживает фокус, Escape закрывает его и возвращает фокус.
- [ ] Screen reader объявляет loading/unavailable/error/success.
- [ ] Без env URL все варианты временно недоступны, страница не ломается.
- [ ] С каждым реальным URL status становится available.
- [ ] Перед handoff показаны правильные version, format, size и requirements.
- [ ] Android начинает загрузку реального APK; AAB не обозначен как устанавливаемый APK.
- [ ] TestFlight открывает правильную invite-страницу.
- [ ] Source/docs скачиваются и совпадают с опубликованным SHA-256.
- [ ] При удалённом/просроченном URL видна ошибка и работает повторная попытка.
- [ ] В аналитике появляются все пять `mywave_event_app_*` событий.

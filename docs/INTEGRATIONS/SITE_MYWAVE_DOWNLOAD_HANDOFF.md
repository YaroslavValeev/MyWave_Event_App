# Письмо разработчикам сайта Site_MyWave

Дата: 2026-09-16  
Версия фактов: Event App **0.5.10** в git (коммит `6ce503b`, ветка `cursor/p0-import-center-athlete-link`)  
От: команда MyWave Event App  
Кому: разработчики сайта (раздел «Проекты» → «Чек-лист организатора»)  
Тема: точный контракт выдачи MyWave Event App — без фиктивных APK

Ниже текст **для копирования в почту**. Не сокращать статусы файлов: они специально разные.

---

## Текст письма

Коллеги,

нужна совместная точка входа для организаторов: **сайт** остаётся витриной отрасли, **MyWave Event App** — source of truth соревнования и выдачи приложения.

Просьба не копировать архивный Flask Download Center (`releases/download-center-2026-08-02/` в репозитории Event App). Это архив 2026-08-02, не runtime.

### Что является фактом на 2026-09-16

| Артефакт | Статус | Что делать на сайте |
|----------|--------|---------------------|
| Веб-приложение Event App (PWA) | **есть** | Вести пользователя сюда |
| Документация установки | **есть** | Можно давать «Скачать документацию» через API Event App **после** деплоя 0.5.10 |
| Android APK/AAB | **нет** | Не показывать живую кнопку скачивания. Подпись: «Сборка готовится» / «Файл временно недоступен» |
| iOS / TestFlight | **нет** | То же |
| ZIP исходников | **нет** | То же |

Нативные сборки Android и iOS **запланированы**, но **после** отладки текущего PWA. Пока их нет в Git и нет URL. Литералы `{{android_download_url}}`, `{{ios_testflight_url}}`, `{{source_archive_url}}` — это имена слотов в env Event App, **не href**.

Документация: если `MYWAVE_EVENT_APP_DOCUMENTATION_URL` пустой или равен `{{documentation_url}}`, Event App сам отдаёт bundled HTML `/downloads/install-and-run.html`. Это реальный файл, не заглушка.

### Staging vs git (важно не перепутать)

- В git уже **0.5.10**: страница `/projects/checklist-org#mywave-event-app`, API `/api/v1/app-downloads/*`.
- На staging VPS `62.113.42.227` по проверке **2026-09-15** крутился образ **0.5.9**. Каталог выдачи там **может ещё отсутствовать**, пока владелец не задеплоит 0.5.10.
- Staging web: `http://62.113.42.227:3001`
- Staging API: порт **8001** на том же хосте (compose staging).
- Production Event App **не менять** этим письмом.
- Гостевая витрина staging сейчас пустая: события в `draft`. Это нормально.

Пока 0.5.10 не подтверждён на staging (`GET /api/v1/app-downloads/manifest` → 200), **не деплойте** на сайт вариант B (прямой вызов API). Используйте вариант A на URL, который владелец подтвердит после деплоя.

### Как встроить блок (вариант A — обязателен на этот спринт)

На странице сайта `/projects/checklist-org`:

1. Блок с заголовком **«MyWave Event App»** и якорем `id="mywave-event-app"` (чтобы работала ссылка `#mywave-event-app`).
2. Короткий текст по-русски, без обещания APK:
   «Цифровая платформа соревнований: заявка, старт, судейство и протокол. Сейчас открывается в браузере телефона. Сборки Android и iOS появятся в этой же карточке, когда файлы будут опубликованы.»
3. Кнопка **«Открыть приложение»** (не «Скачать APK») ведёт на Event App:
   - после деплоя 0.5.10 на staging: `http://62.113.42.227:3001/projects/checklist-org#mywave-event-app`
   - production URL Event App — когда владелец его назначит; до этого production-кнопку не включать.
4. Не ставить `href="{{android_download_url}}"`.
5. Стиль — текущий MyWave сайта, русский UI, контраст, фокус, 320–860 px.

Так сайт не хранит URL файлов и не расходится со статусом сборок.

### Вариант B (после появления 0.5.10 на том API, который зовёт сайт)

Только если origin сайта добавлен в `CORS_ORIGINS` Event App и manifest отвечает 200.

| Метод | Путь | Что внутри |
|-------|------|------------|
| GET | `/api/v1/app-downloads/manifest` | метаданные **без** целевых URL |
| GET | `/api/v1/app-downloads/{id}/status` | `id`: `android` \| `ios` \| `source` \| `documentation` |
| POST | `/api/v1/app-downloads/{id}/handoff` | `location` **только после** подтверждения пользователем |
| POST | `/api/v1/analytics/events` | события ниже |

Ожидаемые `state` на сегодняшней конфигурации 0.5.10 без native URL:

- `documentation` → `available`
- `android`, `ios`, `source` → `unavailable`

Кнопка скачивания активна **только** при `state === "available"`. Для unavailable — текст «Файл временно недоступен», без битой ссылки.

Ошибка API:

```json
{ "error": { "code": "artifact_unavailable", "message": "…" } }
```

Handoff: не больше 20 запросов с IP в минуту; `Cache-Control: no-store`.  
Не проксировать `location` своим бэкендом к произвольным URL (SSRF).  
UI-референс: `apps/web/src/components/AppDownloadCard.tsx` в репозитории Event App.

Аналитика (имена точные):

- `mywave_event_app_card_viewed`
- `mywave_event_app_platform_selected`
- `mywave_event_app_download_clicked`
- `mywave_event_app_download_succeeded`
- `mywave_event_app_download_failed`

`download_succeeded` = сервер отдал handoff, не «файл докачался в браузере».

### Что сайт не делает

- не кладёт APK/IPA в Git;
- не копирует Flask-патч из архива;
- не пишет, что приложение уже в Google Play / App Store;
- не дублирует список URL сборок у себя «на всякий случай».

Когда появятся реальные Android/TestFlight, **меняем только env Event App**. Сайт при варианте A не меняется; при варианте B кнопки сами станут `available`.

### Чек-лист приёмки блока на сайте

- [ ] Якорь `#mywave-event-app` есть
- [ ] Кнопка открывает Event App, а не скачивает несуществующий APK
- [ ] Нет href из плейсхолдеров `{{…}}`
- [ ] Тексты по-русски, без «API/dev»
- [ ] Клавиатура и `focus-visible` на кнопке
- [ ] 320 px и desktop не ломают блок
- [ ] После деплоя 0.5.10: documentation можно получить через Event App; android/ios не кликабельны

Документы: `docs/OPERATIONS/APP_DOWNLOADS.md`, `docs/API/API_CONTRACT.md`, ADR-0009, план отладки `docs/PRODUCT/QA_AND_UX_HARDENING_PLAN.md`.

С уважением,  
команда MyWave Event App

---

## Для внутренней команды Event App

Письмо отправляет **владелец** после того, как решит: слать сейчас с оговоркой «staging ещё 0.5.9» или после деплоя 0.5.10.  
Рекомендация: сначала волна 0 плана отладки (деплой staging), затем это письмо без оговорки про 0.5.9.

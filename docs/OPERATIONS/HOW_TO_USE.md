# Как устроен MyWave Event App и как им пользоваться

Актуально: **2026-08-07**. Продукт локальный (Stage 1), событие seed: **ЧР/ПР Казань 2026** (`chr-pr-kazan-2026`).

---

## 1. Из чего состоит (расклад)

```text
MyWave_Event_App/
├── apps/web/              # Лицо продукта — Next.js (браузер)
├── services/api/          # Мозг — FastAPI + SQLite
│   └── data/mywave_event.db   # Главная БД (после seed)
├── scripts/
│   ├── dev.ps1            # Запуск API + Web
│   ├── reseed.ps1         # Пересобрать БД Казань из Excel
│   └── seed_kazan_2026.py # Импорт Form Excel + слоты + доки + судьи
├── data/
│   ├── mail_outbox/       # Письма OTP/approve, если SMTP не настроен
│   └── documents/         # PDF/Excel документов события (копии)
├── docs/                  # Документация
├── packages/shared-schema/# Черновик общих контрактов
└── releases/              # Архив Download Center (НЕ само приложение)
```

| Слой | Технология | Порт / путь | Роль |
|------|------------|-------------|------|
| **Web** | Next.js App Router | http://127.0.0.1:3000 | UI для людей |
| **API** | FastAPI | http://127.0.0.1:8000 | Auth, события, заявки, файлы |
| **БД** | SQLite | `services/api/data/mywave_event.db` | Единый store |
| **Python venv** | отдельный (кириллица в пути) | `C:\tmp\mw_event_api_venv` | Запуск API/seed/тестов |

**Это не** Site_MyWave / Telegram-плагин. Telegram здесь нет как ядра. SMS OTP — позже; сейчас OTP идёт на **email аккаунта** (+ копия в `mail_outbox`).

### Роли

| Роль | Как получить | Что может |
|------|--------------|-----------|
| `participant` | Регистрация → сразу active | Смотреть событие, подать заявку, профиль |
| `organizer` / `event_admin` / `federation_manager` / `judge` / … | Регистрация → **pending** → approve владельцем | Орган.: заявки участников, approve ролей; судья: вход после approve |
| `platform_admin` | Seed: `y.valeev@gmail.com` + телефон `+79160117179` | Всё админское |

### Данные Казани после `npm run reseed` (эталон)

| Сущность | Кол-во (последний seed) |
|----------|-------------------------|
| Участники (строки заявок Form) | **97** |
| Категории | **17** |
| Медфлаг `has_medical_cert` | **51** |
| Судьи/официалы | **11** |
| Тренировочные слоты | **162** (35 booked) |
| Phone-логины спортсменов | **83** |

Источник участников: Excel ответов Google Form  
`Предварительная регистрация ЧР и ПР 2026 - доски (Ответы) (1).xlsx`.  
Медссылки Drive хранятся **внутри БД**, в публичном API наружу только bool `has_medical_cert` (без URL и без телефона).

---

## 2. Страницы Web (что открывать)

База: **http://127.0.0.1:3000**

| URL | Для кого | Что делает |
|-----|----------|------------|
| `/` | Все | Старт / вход в продукт |
| `/register` | Новый пользователь | Телефон + email + роль. Участник входит сразу. Если телефон/email занят — ссылка «Войти» |
| `/login` | Существующий | Телефон → OTP (в development код часто виден в ответе API / outbox) |
| `/profile` | Вошедший | Сменить ФИО / телефон |
| `/events` | Вошедший | Список событий |
| `/events/1` | Вошедший | Карточка Казани: табы **Обзор / Участники / Слоты / Документы / Заявки** |
| `/events/new` | Организатор+ | Создать событие |
| `/admin/approvals` | Организатор / admin | Очередь ролей (judge и т.д.) |
| `/notifications` | Вошедший | Журнал статусов заявок/ролей (без SMTP) |
| `/health` | Все | Статус связи с API |

API-справка: http://127.0.0.1:8000/docs  
Health API: http://127.0.0.1:8000/health

---

## 3. Как пользоваться по сценариям

### A. Запуск (каждый день)

```powershell
cd "F:\Проекты MyWave\NEW2026\App Champ\MyWave_Event_App"
npm run dev
```

Откроются 2 окна (API + Web). Браузер → http://127.0.0.1:3000

Только web (если API уже крутится после reseed):

```powershell
npm run dev:web
```

### B. Владелец / админ

1. Войти телефоном **`+79160117179`** на `/login`  
   - OTP: смотреть `data\mail_outbox\` или при `APP_ENV=development` поле `dev_otp` в ответе API.  
2. Либо локальный обход (только development):

```powershell
curl.exe -X POST http://127.0.0.1:8000/api/v1/auth/dev-login -H "Content-Type: application/json" -d "{\"email\":\"y.valeev@gmail.com\",\"role\":\"platform_admin\"}"
```

Токен положить в браузер вручную неудобно — проще phone OTP или UI после регистрации.

Организатор-демо: `organizer@example.com` через **dev-login** → роль `organizer`.

Дальше:
- `/admin/approvals` — утвердить судью / комментатора
- `/notifications` — статусы заявок и ролей, пока SMTP не настроен
- `/events/1` → вкладка **Заявки** — принять/отклонить заявки на участие
- `/events/1` → **Участники** — roster + «мед ✓ / мед —»

### C. Спортсмен (участник)

1. `/register` — роль «Участник» → сразу в системе  
   *или* если телефон уже в seed: `/login` по своему номеру из Form Excel  
2. `/events` → Казань → вкладка **Заявки** → подать заявку  
3. Ждёт accept организатора (после accept попадает в публичный roster)

Seed-аккаунты: email вида `p7916…@participants.mywave.local` — для OTP без SMTP письмо не уйдёт на реальную почту спортсмена; код берите из **outbox** / `dev_otp`.

### D. Обновить состав из новой выгрузки Form

1. Положить/обновить Excel по пути, который читает `scripts/seed_kazan_2026.py` (`DEFAULT_FORM_REG`), **или** вызвать seed с `--registration "полный\путь.xlsx"`.
2. Выполнить:

```powershell
cd "F:\Проекты MyWave\NEW2026\App Champ\MyWave_Event_App"
npm run reseed
```

Скрипт сам гасит API → `--reset-db` → seed → поднимает API.  
**Важно:** `--reset-db` стирает локальную БД; ручные правки в SQLite пропадут (owner-телефон seed снова привязывает).

### E. Тесты

```powershell
npm run test:api
```

Ожидаемо: **22 passed**.

---

## 4. Что делает только владелец (не агенты)

1. **SMTP Gmail** — реальные письма OTP/approve → см. [OWNER_COMMANDS.md](./OWNER_COMMANDS.md) §4  
2. **Staging / прод deploy** → [SERVER_COMMANDS.md](./SERVER_COMMANDS.md)  
3. По желанию: подставить реальные email спортсменам вместо `*.mywave.local`

Без SMTP всё уже работает локально через `data/mail_outbox/`.

---

## 5. Быстрая шпаргалка команд

| Действие | Команда |
|----------|---------|
| Старт | `npm run dev` |
| Reseed Казань | `npm run reseed` |
| Тесты | `npm run test:api` |
| Только Web | `npm run dev:web` |
| Смотреть OTP-письма | `Get-ChildItem data\mail_outbox \| Sort LastWriteTime -Descending \| Select -First 5` |

Ещё короче по командам: [OWNER_COMMANDS.md](./OWNER_COMMANDS.md).  
Статус продукта: [../STATUS/CURRENT_STATE.md](../STATUS/CURRENT_STATE.md).

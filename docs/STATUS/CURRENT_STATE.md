# CURRENT_STATE

Дата: 2026-08-27  
Версия продукта: **0.5.7**  
Путь до DoD v1 (аудит): ~**80%**

Сверка с прикреплёнными DOCX: [GAP_VS_ATTACHED_DOCS.md](./GAP_VS_ATTACHED_DOCS.md) — **не всё из экосистемы/Hub относится к этому репо**.

## Работает

- Remote + CI + release + staging runbook.
- Auth / roles / consent / notifications / applications / roster / training slots.
- Documents, checklist, heats / start list / runs.
- Results draft → verified → published → void.
- Rules catalog + EventRulesProfile (FVLS/IWWF).
- ProtocolCapture (фото/PDF).
- Structured scoring, official protocol export, Athlete ID, archive lock.
- **UX 0.5.6:** публичная витрина событий (J4); ролевые вкладки; русские статусы; вход без dev-console; регистрация участником по умолчанию; нижняя навигация на телефоне.
- **UX 0.5.7:** светлая тема, бирюзовые обводки и тени кнопок. Просроченный токен не тупик: гостевой просмотр + «Войти снова» с возвратом. Ролевые пути закрыты CTA (создание события, доступы, профиль, уведомления). GET heats публичный на витрине (start list по-прежнему с входом).

## Частично / нет

- Media / ParserNews / broadcast
- Score-now / Excel import adapters
- PDF export (HTML → Print пока достаточно)
- SMTP + remote staging host — owner
- Telegram/MAX/native — не Stage 1 этого репо
- Native iOS/Android — нет (PWA)
- Полевой dry-run судья+организатор на площадке — не выполнен

## Следующий P0 (код)

1. Pilot dry-run одного события на площадке (судья + организатор)
2. PDF protocol export (optional)
3. Deep-link уведомлений в конкретную заявку

## Проверки

- pytest: public events + invalid bearer as guest + guest heats
- UI: светлый фон; бирюза на кнопках; истекшая сессия → «Войти снова»

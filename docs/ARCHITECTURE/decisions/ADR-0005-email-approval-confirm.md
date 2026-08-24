# ADR-0005: Email role approval requires explicit POST confirm

Дата: 2026-08-24  
Статус: accepted

## Контекст

GET-ссылки `/api/v1/auth/approvals/{token}/approve|reject` сразу меняли статус заявки. Почтовые сканеры, превью клиентов и утечка URL в логах могли утвердить или отклонить роль без намерения владельца.

Очередь `/auth/approvals/pending` отдавала сырой token в JSON — лишняя поверхность для утечки capability-секрета.

## Решение

1. GET по email-ссылке только показывает HTML-форму подтверждения. Статус не меняется.
2. Мутация — `POST /api/v1/auth/approvals/{token}/confirm` с полем формы `decision=approve|reject`.
3. UI организатора утверждает по `approval_id`: `POST /api/v1/auth/approvals/{approval_id}/approve|reject` (Bearer).
4. Список pending больше не возвращает `token`.

GET без побочного эффекта закрывает типичный prefetch CSRF у email-ссылок. Сам token в URL остаётся capability-секретом; это приемлемо для Stage 1, пока SMTP не в production.

## Последствия

- Старые письма с GET-ссылками продолжают открываться, но требуют клика «Подтвердить».
- Тесты и UI больше не полагаются на GET-мутацию.
- Нужен in-app журнал уведомлений, потому что почта по-прежнему может не доходить.

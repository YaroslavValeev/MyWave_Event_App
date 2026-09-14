# Privacy and Consent

**Дата:** 2026-08-04  

## 1. Категории данных

| Категория | Примеры | Правовое основание (рабочая модель) |
|-----------|---------|--------------------------------------|
| Account | email, display_name, password_hash | договор / регистрация |
| Event participation | заявка, bib, команда | исполнение услуги события |
| Results | спортивные результаты | публичный интерес мероприятия + согласие на публикацию |
| Audit | IP truncated, actor id, action | законный интерес безопасности |
| Analytics | event ids, counters | согласие / anonymized |

## 2. Согласия (ConsentRecord)

Минимальные purposes:

- `terms_of_use`
- `privacy_policy`
- `publish_name_and_results` (для публичной витрины)
- `product_analytics` (опционально)

Реализация Stage 1 (2026-08-24): таблица `consent_records`, обязательные purposes блокируют регистрацию, опциональные управляются в `/profile`. Без `publish_name_and_results` self-serve ФИО на roster заменяется на «Участник №id». Импорт организатора не маскируется. ADR-0004.

Заполненные таблицы участников, телефоны, полные даты рождения и медицинские документы **не коммитятся** в git. Import Center хранит их только в БД инсталляции; в JSON API телефон маскируется, URL медсправок не сохраняются.

Хранить: `user_id`, `purpose`, `version`, `granted_at`, `revoked_at`.

## 3. Публикация

- Без `publish_name_and_results` — на витрине псевдоним / «Участник #N» (policy события).
- Гость не видит email/phone.

## 4. Retention (черновик)

| Данные | Срок |
|--------|------|
| Account inactive | 24 мес → review delete |
| Audit | 12–24 мес |
| Analytics raw | 13 мес |
| Backups | см. BACKUP_RESTORE.md |

## 5. Права субъекта

- Export своих данных (Stage 2+ endpoint).
- Удаление аккаунта с анонимизацией результатов по политике события.

## 6. Кросс-системы

Не передавать PII в Telegram/MAX адаптеры без отдельного consent и минимизации.

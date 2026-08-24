# Changelog

## 0.4.0 — 2026-08-24

- Email-ссылки approve/reject больше не меняют статус по GET: нужна POST-форма подтверждения (ADR-0005).
- Очередь ролей в API не отдаёт raw token; UI утверждает по `approval_id`.
- In-app журнал уведомлений: заявка/роль видны в `/notifications` без SMTP.
- Лимит OTP: 5 запросов на номер за 10 минут.
- Production отказывается стартовать с дефолтным/коротким `SECRET_KEY`.
- Удалены неиспользуемые `app/schemas.py` и `app/services/core.py`.
- Версии синхронизированы до `0.4.0` (root/web/api).
- Release discipline + staging runbook (`RELEASE.md`, `STAGING.md`, `docker-compose.staging.yml`, workflow `release.yml`).
- Roadmap: Competition Platform DoD v1 (подготовка → archive без Excel SoT).
- Pytest: **36 passed**. Next.js build: passed (в т.ч. `/notifications`).

## 0.3.0 — 2026-08-24

- Минимальный контур согласий Stage 1: `ConsentRecord`, каталог `docs/LEGAL/*`, публичный API документов.
- Регистрация требует `terms_of_use` и `privacy_policy`; опционально публикация имени и аналитика.
- Профиль: просмотр/выдача/отзыв опциональных согласий; обязательные нельзя отозвать.
- Публичный roster маскирует ФИО self-serve заявок без publish-consent (`Участник №id`); импорт организатора без изменений.
- Audit: `consent.granted` / `consent.revoked`.
- ADR-0004. Pytest: 29 passed.

## 0.2.0 — 2026-08-05

- Домен соревнования: категории, участники, документы.
- Seed ЧР/ПР Казань 2026 из Excel/PDF организатора (без телефонов/медссылок).
- UI карточки события `/events/[id]`.
- `npm run dev` — однокомандный локальный запуск.

## 0.1.0 — 2026-08-04

- Инициализация standalone-репозитория MyWave Event App.
- Архивация Download Center в `releases/download-center-2026-08-02/`.
- Stage 1 API: health/ready, JWT dev-login, roles, events, audit.
- Stage 1 Web/PWA shell.
- Канонические документы и серверные команды.

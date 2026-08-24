# ADR-0002: Stage 1 tech stack

Дата: 2026-08-04  
Статус: accepted

## Решение

- Web/PWA: Next.js + TypeScript
- API: FastAPI + Python
- DB: SQLite (local Stage 1) → PostgreSQL compatible via `DATABASE_URL`
- Auth foundation: JWT; dev-login только при `APP_ENV=development`
- Deploy: Docker Compose + systemd-ready commands

## Почему

Соответствует Master Prompt ориентиру и позволяет быстро закрыть Этап 1 без привязки к Flask-монолиту сайта.

# ADR-0016 — Live Scoreboard (SSE + polling fallback)

Дата: 2026-11-04  
Статус: accepted  
Связь: Result SoT, scoring_service, ADR-0003

## Контекст

JudgeScore / Result уже есть. Нет realtime scoreboard и отдельного projection API.

## Решение

1. **Не** создавать второй Scoring Engine. SoT остаётся `Result` + `JudgeScore` + rules profile.
2. `GET /api/v1/events/{id}/scoreboard` — снимок опубликованных (и опционально verified для staff) результатов + `revision`.
3. `GET /api/v1/events/{id}/scoreboard/stream` — **SSE** (`text/event-stream`) с периодическим push при смене `revision`.
4. Клиент: `EventSource` + fallback polling 5–10 с.
5. Зритель/гость видит только `published`. Staff может запросить `include_unofficial=true`.

## Offline

Ввод оценок offline — очередь на клиенте (Stage 3 / OFFLINE_SYNC); scoreboard без сети показывает последний кеш и пометку «не актуально».

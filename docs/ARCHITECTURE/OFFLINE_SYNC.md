# Offline Sync — целевая модель

**Дата:** 2026-08-04  
**Статус Stage 1:** online-only (документ — контракт будущего Stage 3)

## 1. Зачем

Судейство и расписание на площадке с нестабильной сетью. Offline не нужен для гостя публичной витрины Stage 1.

## 2. Scope Stage 3 (черновик)

| Режим | Данные | Поведение |
|-------|--------|----------|
| Read-cache | published Event, Session, Entry list | Cache-first, TTL + ETag |
| Write-queue | Result drafts | Outbox на клиенте → flush при online |
| Forbidden offline | publish result, смена ролей, delete event | Только online |

## 3. Конфликты

- Optimistic concurrency: поле `Result.version`.
- При 409 клиент показывает diff: server vs local draft; победитель — явный выбор судьи/админа (не last-write-wins молча).
- `published` результаты не перезаписываются из offline queue без нового draft.

## 4. Идентификаторы

- Клиент может генерировать UUID для draft Result.
- Сервер идемпотентен по `Idempotency-Key` / client_generated_id.

## 5. Хранилище клиента

- IndexedDB (PWA).
- Не дублировать SoT: кэш помечается `sourced_from=api` + `synced_at`.

## 6. Не делать сейчас

- CRDT / full multi-master.
- Sync через Telegram.
- Offline auth refresh без secure storage policy.

## 7. Критерий готовности offline v1

- Судья создаёт draft offline, публикует online.
- Конфликт 409 воспроизведён тестом.
- Документ обновлён фактическим протоколом wire format.

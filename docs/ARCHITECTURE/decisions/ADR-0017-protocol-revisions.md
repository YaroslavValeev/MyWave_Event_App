# ADR-0017 — Official Protocol Revisions

Дата: 2026-11-04  
Статус: accepted  
Связь: official-protocol live export, ResultHistory

## Контекст

Live `GET .../official-protocol` каждый раз собирает bundle из текущей БД. После void/re-publish старый PDF нельзя воспроизвести.

## Решение

1. Сохранить live-export endpoints как **рабочий просмотр**.
2. Добавить сущность `OfficialProtocolRevision`: immutable snapshot JSON + `revision_no` + статус `approved` + автор + note.
3. `POST .../official-protocol/revisions` (organizer+) фиксирует снимок; не перезаписывает предыдущие.
4. При коррекции результатов после утверждения — новая ревизия (или явный correction note), без тихой перезаписи.
5. PDF-native generation (WeasyPrint и т.п.) — optional later; сейчас snapshot JSON + существующий HTML renderer по snapshot.

## Запрещено

Называть live-export «утверждённым официальным» без записи ревизии.

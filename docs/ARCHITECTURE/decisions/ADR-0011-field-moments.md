# ADR-0011 — Полевые моменты (камера PWA)

**Дата:** 2026-09-17  
**Статус:** accepted (срез 1: съёмка в браузере, не эфир)  
**Владелец:** MyWave Event App

## Контекст

Организатору нужен насыщенный транслируемый контент: бэкстейдж, взгляд пилота катера, маршал на старте, эмоции площадки. Это не протокол судьи (`ProtocolCapture`) и не полный media journey (EXIF, Athlete ID, consent-публикация).

Нативные оболочки камеры ещё не собираем. На staging HTTP; `getUserMedia` часто требует HTTPS. На телефоне надёжный путь Stage 1 — `<input capture>` (системная камера → файл → API).

## Решение

1. Отдельная сущность **FieldMoment**, не смешивать с official protocol.
2. Съёмка и просмотр — роли: `media`, `commentator`, `support`, organizer+, `chief_judge`. Участник — **403**.
3. Точка съёмки (`pov`): `backstage` | `boat_pilot` | `start_marshal` | `on_water` | `crowd` | `other`.
4. Статусы: `draft` (команда события) → `approved` (можно отдать в эфир позже) → `withheld` (спрятать). Гость и витрина файлы не получают.
5. Файлы: JPG/PNG/WebP/HEIC/MP4/WebM/MOV; фото ≤15 МБ, видео ≤40 МБ; path containment `data/field-media/{slug}/`; audit.
6. Публикация в соцсети, EXIF-match, согласие медиа, прямая трансляция — **не** этот срез (волна после полевого dry-run / native HTTPS).

## Последствия

- Камера в PWA работает без APK.
- На HTTP staging открывается системная камера через file input, не live-превью в странице.
- Broadcast/commentator читает approved моменты, не пишет результаты.

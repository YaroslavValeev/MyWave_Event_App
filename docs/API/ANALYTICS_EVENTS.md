# Analytics Events

**Дата:** 2026-09-16  
**Префикс:** `mwe_` (MyWave Event) + события выдачи `mywave_event_app_*`

События продукта. Транспорт Stage 1: `POST /api/v1/analytics/events`.

## 1. Транспорт Stage 1–2

- Клиент: `window`/SDK → POST `/api/v1/analytics/events` (одно событие).
- Сервер: пишет в Audit (`analytics.<event>`) и stdout; неизвестные имена — 400.
- PII в properties запрещены (только allowlisted keys: ids, stage, reason, version).

## 2. Каталог

| Event name | Когда | Props (минимум) |
|------------|-------|-----------------|
| `mwe_app_opened` | старт web shell | `app_version`, `channel=web` |
| `mwe_auth_login_succeeded` | успешный login | `user_id_hash` |
| `mwe_auth_login_failed` | ошибка login | `reason_code` |
| `mwe_event_viewed` | открыта карточка события | `event_id` |
| `mwe_event_created` | создано событие | `event_id` |
| `mwe_event_published` | publish | `event_id` |
| `mwe_entry_submitted` | заявка отправлена | `event_id`, `entry_id` |
| `mwe_notification_opened` | открыт журнал уведомлений | `unread_count` |
| `mwe_consent_granted` | пользователь выдал согласие | `purpose`, `version` |
| `mwe_consent_revoked` | пользователь отозвал согласие | `purpose`, `version` |
| `mwe_legal_document_viewed` | открыт текст документа | `purpose`, `version` |
| `mwe_result_draft_saved` | черновик результата | `event_id`, `result_id` |
| `mwe_roster_locked` | состав зафиксирован | `event_id` |
| `mwe_result_published` | результат опубликован (chief judge) | `event_id`, `result_id` |
| `mwe_permission_denied` | 403 на UI/API | `route_or_action` |
| `mwe_sync_flush_succeeded` | (Stage 3) offline flush | `count` |
| `mwe_sync_conflict` | (Stage 3) 409 | `entity_type` |
| `mywave_event_app_card_viewed` | карточка выдачи попала в viewport | `app_id` |
| `mywave_event_app_platform_selected` | выбран Android / iOS / source / docs | `artifact_id` |
| `mywave_event_app_download_clicked` | нажата кнопка скачивания | `artifact_id`, `version` |
| `mywave_event_app_download_succeeded` | handoff успешен, старт перехода | `artifact_id`, `version` |
| `mywave_event_app_download_failed` | ошибка манифеста, status или handoff | `artifact_id`, `stage`, `reason` |

`download_succeeded` означает успешный handoff, не завершение браузерной загрузки стороннего файла.

## 3. Download Center (архив Flask)

Архивный патч сайта: `releases/download-center-2026-08-02/`. Runtime выдачи с 0.5.10 — этот API. Сайт не дублирует URL, см. `docs/INTEGRATIONS/SITE_MYWAVE_DOWNLOAD_HANDOFF.md`.

## 4. Privacy

- Consent на продуктовую аналитику — см. PRIVACY_AND_CONSENT.md.
- Без consent — только технические health metrics без user id.
- Ingest выдачи не пишет email/телефон: extra keys из payload отбрасываются.

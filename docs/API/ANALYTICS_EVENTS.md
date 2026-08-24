# Analytics Events

**Дата:** 2026-08-04  
**Префикс:** `mwe_` (MyWave Event)  

События продукта (не путать с Download Center `mywave_event_app_*` на сайте).

## 1. Транспорт Stage 1–2

- Клиент: `window`/SDK → POST `/api/v1/analytics/events` (batch).
- Сервер: пишет в Audit/analytics table или stdout sink в dev.
- PII в properties запрещены (только ids).

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
| `mwe_result_published` | результат опубликован | `event_id`, `result_id` |
| `mwe_permission_denied` | 403 на UI/API | `route_or_action` |
| `mwe_sync_flush_succeeded` | (Stage 3) offline flush | `count` |
| `mwe_sync_conflict` | (Stage 3) 409 | `entity_type` |

## 3. Download Center (архив, внешний сайт)

События `mywave_event_app_card_viewed` и др. относятся к **сайтовому** Download Center и документированы в архиве `releases/download-center-2026-08-02/`. В runtime этого приложения их не эмулировать.

## 4. Privacy

- Consent на продуктовую аналитику — см. PRIVACY_AND_CONSENT.md.
- Без consent — только технические health metrics без user id.

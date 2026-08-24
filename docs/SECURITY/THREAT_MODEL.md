# Threat Model (lightweight)

**Дата:** 2026-08-04  
**Метод:** упрощённый STRIDE для Stage 1  

## 1. Активы

- Учётные записи и credentials.
- Результаты соревнований (целостность/время публикации).
- PII участников.
- Роли организаторов/судей.
- Backup files.

## 2. Точки входа

- Public HTTP API / Web.
- Admin endpoints.
- Upload artifact endpoints (позже).
- Server SSH / reverse proxy (ops).
- Украденный JWT.

## 3. Угрозы и контрмеры

| ID | Угроза | Контрмера |
|----|--------|-----------|
| T1 | Credential stuffing | rate limit, strong hash, lockout policy |
| T2 | Privilege escalation (athlete→admin) | server-side membership checks |
| T3 | Подделка результата | audit, version lock, publish gate |
| T4 | IDOR по event/entry id | authz на каждый объект |
| T5 | XSS в Web | React escape, CSP roadmap, sanitize rich text |
| T6 | CSRF | SameSite cookies / CSRF token если cookie session |
| T7 | Утечка через логи | redaction email/token |
| T8 | Backup theft | encrypt at rest, ограниченный ACL |
| T9 | Supply chain npm/pip | lockfiles, review deps |
| T10 | Путаница с Download Center deploy | отдельные SERVER_COMMANDS; нет секретов сайта |

## 4. Out of scope Stage 1

- Formal pen-test report.
- Hardware attack on devices.
- Nation-state targeted attack modeling.

## 5. Review trigger

Пересмотр threat model при: выходе в internet production, добавлении адаптеров Telegram/MAX, появлении native mobile, платежей.

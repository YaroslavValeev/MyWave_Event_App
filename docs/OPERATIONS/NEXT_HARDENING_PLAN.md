# План дожима staging / DoD v1 (2026-11-01)

## Цель

Закрыть всё, что можно кодом и ops-доками до полевого пилота. Пилот на площадке и боевые секреты SMTP — только владелец.

## Порядок

| # | Шаг | Кто | Статус |
|---|-----|-----|--------|
| 1 | DATA_DIR=/data в Docker (mail_outbox рядом с БД) | код 0.5.14 | в этом релизе |
| 2 | Compose profile `ollama` + сеть `ai-team_default` | код 0.5.14 | в этом релизе |
| 3 | `scripts/staging_up.sh` — up + network + health | код 0.5.14 | в этом релизе |
| 4 | Runbook: туннель SSH, UFW, диск, SMTP, nginx-пример | docs | в этом релизе |
| 5 | `/health` отдаёт `version` | код 0.5.14 | в этом релизе |
| 6 | Owner: SMTP в `.env.staging` + перезапуск api | owner | pending |
| 7 | Owner: публичный URL (nginx/домен) или стабильный туннель | owner | pending |
| 8 | Owner: `docker system prune` при диске ≥85% | owner | pending |
| 9 | Owner: полевой dry-run судья+организатор | owner | **блокер DoD v1** |
| 10 | Media / FieldMoment / STT | код Stage 5+ | после пилота |
| 11 | Live board polish / PDF protocol | код optional | после пилота |

## Критерий «staging hardened»

- [ ] `curl /health` → `version` = текущий semver, `db_ok` true  
- [ ] OTP: либо SMTP delivered, либо файл в `/data/mail_outbox`  
- [ ] EventReport assemble → `AI: openai` при profile ollama (или cloud proxy)  
- [ ] Web доступен: публичный URL **или** документированный SSH `-L`  
- [ ] Диск < 85% после prune  

## Rollback

`git checkout` предыдущего tag / `docker compose ... up -d --build` с прошлым SHA. Volume `staging_api_data` не удалять.

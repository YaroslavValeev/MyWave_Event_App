# ADR-0006 — Governing bodies, disciplines, scoring profiles

**Дата:** 2026-08-25  
**Статус:** accepted (owner input)

## Контекст

MyWave Event App должен проводить соревнования под разными организациями и дисциплинами, с выбором режима скоринга (structured / manual / photo protocol). FVLS-события для **официального протокола** всегда под эгидой IWWF.

Score-now (IWWF cable) — желательный adapter; обязательна **встроенная альтернатива** с теми же правилами расчёта.

## Решение

### 1. Governing Body (каталог)

| Код | Название | Роль в Event App |
|-----|----------|------------------|
| `FVLS` | ФВЛС | primary org для РФ-событий |
| `IWWF` | IWWF | **обязательный sanction layer** для официального протокола FVLS |
| `WSWS` | World Series of Wake Surfing | rule pack wakesurf (boat), DRIVE scoring |
| `WWA` | World Wake Association | membership/affiliation (WSWS ссылается на WWA) |
| `CWSA` | CWSA | reserved, rule pack позже |

**Правило FVLS:** `governing_body=FVLS` + `sanction=IWWF` всегда для published official protocol.

### 2. Priority disciplines (P0)

| Код | RU | Rule pack (P0) |
|-----|-----|----------------|
| `wakeboard_boat` | Вейкборд (катер) | `IWWF_BOAT_EIC_2025` |
| `wakeboard_cable` | Cable wakeboard / электротяга | `IWWF_CABLE_TI_2025` (Score-now alt) |
| `wakesurf_boat` | Вейксерф | `IWWF_WAKESURF_2024` **или** `WSWS_WAKESURF_DRIVE` |
| `wakeskim` | Вейкским | `ORG_CUSTOM_v1` (manual/photo until rules digitized) |

Waterski (figures/slalom/jump), wakefoil, longboard — **P2**, не блокируют первый реальный старт.

### 3. Scoring modes

| Mode | UX | Official? |
|------|-----|-----------|
| `structured` | Judge panel в app | да, после verify |
| `manual` | Organizer вводит score/place | да, после verify |
| `photo_protocol` | Фото/PDF листа → review → publish | да, **только после human verify** |
| `import_scorenow` | CSV/export adapter | да, после verify |
| `import_excel` | WSWS Excel / org template | да, после verify |

### 4. Photo / document capture (P0 UX)

Минимальный контур «удобно и просто»:

- На событии: **Документы** (уже есть upload PDF/XLSX).
- Новая зона **Протокол / Judge sheet**:
  - `Сфотографировать` (mobile camera, `<input capture="environment">`)
  - `Загрузить файл` (JPEG/PNG/PDF)
  - Preview → привязка к heat/run/category → **черновик** → verify chief/organizer → publish
- OCR/LLM extract — **assist only**, не auto-publish.

Canonical source WSWS RU: `Site_MyWave/static/docs/rules/wsws_wakesurf_rules_ru.docx` (mirror в Event App docs при релизе rule pack).

### 5. Scoring engines (plugin)

```
ScoringEngineId → calculate(JudgeInput[], RunContext) → ScoringResult
ScoringResult: { total_score, criteria{}, placement_hint, audit_payload }
```

P0 engines:

- `IWWF_CABLE_TI` — 3 judges, Technical + Impression, best of 2 runs, avg, no tie in heat
- `IWWF_BOAT_EIC` — E/I/C 0–10 → weighted 100, placement override, 2-of-3 rule
- `WSWS_DRIVE` — Difficulty, Risk, Intensity, Variety, Execution; one score per run; scribe + chief; Excel/judge sheets workflow
- `MANUAL_PLACE` — score + place без formula (wakeskim interim)

### 6. Score-now strategy

| Если | Действие |
|------|----------|
| API доступен | `ScoreNowAdapter` sync import/export |
| API нет | **MyWave Scoring** = native `IWWF_CABLE_TI` + heat/seeding parity |
| IWWF sanctioned event | export bundle для ручной загрузки в Score-now (interim) |

## Источники правил (owner files)

| Файл | Назначение |
|------|------------|
| `Site_MyWave/.../wsws_wakesurf_rules_ru.docx` | WSWS wakesurf RU |
| `F:\My wave\2024-OFFICIAL-WAKESURF-RULES-FINAL.pdf` | IWWF wakesurf 2024 |
| `F:\My wave\IWWFWakeboardBoatRules-2022.pdf` | IWWF boat (superseded by 2025 online) |
| `F:\My wave\IWWF-Wakeboard-Посев_Участников.pdf` | seeding reference |

## WSWS scoring (из wsws_wakesurf_rules_ru.docx)

- Критерии **DRIVE**: Difficulty, Risk, Intensity, Variety, Execution.
- Один итоговый балл на run (wakesurf); длительность run: Surf Pro/Semi-Pro **4 min**, Skim **2 min**.
- После heat: scribe + chief judge; официальный **WSWS Excel**; допускаются **judge sheets** (фото листов).
- Результаты — до **100** баллов; разрешение расхождений через сравнение sheets.
- Appendix: Variety Calculation Tool, benchmark rider, штрафы (early start / early release).

## Последствия

- `Event.disciplines` (free text) → migrate к `EventDiscipline[]` + `rules_profile_id`.
- `Result.score` становится output engine, не единственным полем ввода.
- Новые сущности: `ProtocolCapture`, `JudgeScore`, `ScoringProfile`, `RulesPack`.

## Критерий готовности P0

- [ ] Wizard: FVLS + IWWF sanction + выбор 1–4 дисциплин P0
- [ ] Photo/upload протокола с verify UI
- [ ] `WSWS_DRIVE` + `IWWF_CABLE_TI` engines (structured)
- [ ] Published protocol PDF/JSON + audit

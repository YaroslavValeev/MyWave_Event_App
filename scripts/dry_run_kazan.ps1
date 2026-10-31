# Virtual E2E dry-run on Kazan seed: heat -> DNS -> result publish -> AI report -> excel.
# Prerequisites: API up, DB seeded (npm run reseed), APP_ENV=development.
#
#   powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\dry_run_kazan.ps1
#   powershell ... -File .\scripts\dry_run_kazan.ps1 -ApiBase http://127.0.0.1:8010

param(
  [string]$ApiBase = "http://127.0.0.1:8010",
  [string]$EventSlug = "chr-pr-kazan-2026"
)

$ErrorActionPreference = "Stop"
Write-Host "== Kazan dry-run against $ApiBase =="

$health = Invoke-RestMethod -Uri "$ApiBase/health" -Method GET
Write-Host "health=$($health.status) db_ok=$($health.db_ok)"

$login = Invoke-RestMethod -Uri "$ApiBase/api/v1/auth/dev-login" -Method POST `
  -ContentType "application/json" `
  -Body (@{ email = "organizer@example.com"; role = "organizer" } | ConvertTo-Json)
$token = $login.access_token
if (-not $token) { throw "dev-login failed" }
$H = @{ Authorization = "Bearer $token"; "Content-Type" = "application/json" }

$events = Invoke-RestMethod -Uri "$ApiBase/api/v1/events" -Headers @{ Authorization = "Bearer $token" }
$event = @($events.items) | Where-Object { $_.slug -eq $EventSlug } | Select-Object -First 1
if (-not $event) { $event = @($events.items) | Select-Object -First 1 }
if (-not $event) { throw "No events. Run npm run reseed" }
$eid = [int]$event.id
Write-Host "event id=$eid slug=$($event.slug) status=$($event.status)"

# Ensure live-ish status for mutations
try {
  Invoke-RestMethod -Uri "$ApiBase/api/v1/events/$eid/status" -Method PATCH -Headers $H `
    -Body (@{ status = "live" } | ConvertTo-Json) | Out-Null
  Write-Host "status -> live"
} catch {
  Write-Host "status patch skipped: $($_.Exception.Message)"
}

$parts = Invoke-RestMethod -Uri "$ApiBase/api/v1/events/$eid/participants" -Headers @{ Authorization = "Bearer $token" }
$roster = @($parts.items) | Where-Object { $_.status -in @("accepted", "registered") } | Select-Object -First 12
if ($roster.Count -lt 2) { throw "Need at least 2 participants in roster" }
Write-Host "roster_sample=$($roster.Count)"

$heatCode = "DRY-$(Get-Date -Format 'HHmmss')"
$heat = Invoke-RestMethod -Uri "$ApiBase/api/v1/events/$eid/heats" -Method POST -Headers $H `
  -Body (@{ code = $heatCode; title = "Dry-run Final"; heat_number = 1 } | ConvertTo-Json)
$hid = [int]$heat.id
Write-Host "heat id=$hid code=$heatCode"

$fill = Invoke-RestMethod -Uri "$ApiBase/api/v1/events/$eid/heats/$hid/start-list/fill" -Method POST -Headers $H -Body "{}"
Write-Host "start_list_total=$($fill.total)"
$entries = @($fill.items)
if ($entries.Count -eq 0) {
  # manual add first two
  $o = 1
  foreach ($p in $roster | Select-Object -First 2) {
    Invoke-RestMethod -Uri "$ApiBase/api/v1/events/$eid/heats/$hid/start-list" -Method POST -Headers $H `
      -Body (@{ participant_id = $p.id; start_order = $o } | ConvertTo-Json) | Out-Null
    $o++
  }
  $sl = Invoke-RestMethod -Uri "$ApiBase/api/v1/events/$eid/heats/$hid/start-list" -Headers @{ Authorization = "Bearer $token" }
  $entries = @($sl.items)
}
$dns = $entries[0]
Invoke-RestMethod -Uri "$ApiBase/api/v1/events/$eid/heats/$hid/start-list/$($dns.id)/status" -Method PATCH -Headers $H `
  -Body (@{ status = "dns" } | ConvertTo-Json) | Out-Null
Write-Host "dns participant_id=$($dns.participant_id)"

$scored = $entries | Where-Object { $_.id -ne $dns.id } | Select-Object -First 1
if (-not $scored) { throw "No second start-list entry for score" }
$draft = Invoke-RestMethod -Uri "$ApiBase/api/v1/events/$eid/results" -Method POST -Headers $H `
  -Body (@{ participant_id = $scored.participant_id; score = 88.5; place = 1; heat_id = $hid } | ConvertTo-Json)
$rid = [int]$draft.id
Invoke-RestMethod -Uri "$ApiBase/api/v1/events/$eid/results/$rid/status" -Method PATCH -Headers $H `
  -Body (@{ status = "verified" } | ConvertTo-Json) | Out-Null
Invoke-RestMethod -Uri "$ApiBase/api/v1/events/$eid/results/$rid/status" -Method PATCH -Headers $H `
  -Body (@{ status = "published" } | ConvertTo-Json) | Out-Null
Write-Host "published result id=$rid"

# void previous report if published
try {
  $cur = Invoke-RestMethod -Uri "$ApiBase/api/v1/events/$eid/event-report" -Headers @{ Authorization = "Bearer $token" }
  if ($cur.status -eq "published") {
    Invoke-RestMethod -Uri "$ApiBase/api/v1/events/$eid/event-report/void" -Method POST -Headers $H -Body "{}" | Out-Null
  }
} catch { }

$report = Invoke-RestMethod -Uri "$ApiBase/api/v1/events/$eid/event-report/assemble" -Method POST -Headers $H `
  -Body (@{ use_llm = $true } | ConvertTo-Json)
Write-Host "report source=$($report.source) ai=$($report.facts.ai.provider) dns=$($report.facts.dns_dnf_count) results=$($report.facts.published_results_count)"

$xlsx = Join-Path $env:TEMP "kazan-dry-run-$eid.xlsx"
Invoke-WebRequest -Uri "$ApiBase/api/v1/events/$eid/event-report/excel" -Headers @{ Authorization = "Bearer $token" } -OutFile $xlsx
Write-Host "excel=$xlsx size=$((Get-Item $xlsx).Length)"

$pub = Invoke-RestMethod -Uri "$ApiBase/api/v1/events/$eid/event-report/publish" -Method POST -Headers $H -Body "{}"
Write-Host "report_status=$($pub.status)"

Write-Host "OK dry-run complete. UI: /events/$eid#report"

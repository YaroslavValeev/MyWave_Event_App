# Smoke EventReport AI + Excel. API must be up on :8000 (development).
#   powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\smoke_event_report.ps1
#   powershell ... -File .\scripts\smoke_event_report.ps1 -EventId 1

param(
  [int]$EventId = 0,
  [string]$ApiBase = "http://127.0.0.1:8000"
)

$ErrorActionPreference = "Stop"
Write-Host "== EventReport smoke against $ApiBase =="

$health = Invoke-RestMethod -Uri "$ApiBase/health" -Method GET
Write-Host "health: $($health.status)"

$loginBody = @{ email = "organizer@example.com"; role = "organizer" } | ConvertTo-Json
$login = Invoke-RestMethod -Uri "$ApiBase/api/v1/auth/dev-login" -Method POST -ContentType "application/json; charset=utf-8" -Body $loginBody
$token = $login.access_token
if (-not $token) { throw "dev-login failed (APP_ENV must be development)" }
$headers = @{ Authorization = "Bearer $token" }

if ($EventId -le 0) {
  $events = Invoke-RestMethod -Uri "$ApiBase/api/v1/events" -Headers $headers
  $first = @($events.items)[0]
  if (-not $first) { throw "No events. Run: npm run reseed" }
  $EventId = [int]$first.id
}
Write-Host "event_id=$EventId"

$assembleBody = @{ use_llm = $true } | ConvertTo-Json
$assemble = Invoke-RestMethod -Uri "$ApiBase/api/v1/events/$EventId/event-report/assemble" `
  -Method POST -Headers ($headers + @{ "Content-Type" = "application/json" }) `
  -Body $assembleBody
$aiProvider = $assemble.facts.ai.provider
Write-Host "assemble source=$($assemble.source) status=$($assemble.status) ai=$aiProvider"

$xlsxPath = Join-Path $env:TEMP "event-$EventId-report.xlsx"
Invoke-WebRequest -Uri "$ApiBase/api/v1/events/$EventId/event-report/excel" -Headers $headers -OutFile $xlsxPath
$len = (Get-Item $xlsxPath).Length
Write-Host "excel path=$xlsxPath size=$len"

$roleUrl = "$ApiBase/api/v1/events/$EventId/role-actions" + "?phase=day"
$actions = Invoke-RestMethod -Uri $roleUrl -Headers $headers
Write-Host "role_actions_day_total=$($actions.total)"

Write-Host "OK"

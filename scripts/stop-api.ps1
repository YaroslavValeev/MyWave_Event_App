#Requires -Version 5.1
<#
.SYNOPSIS
  Stop MyWave Event App API and release SQLite lock on mywave_event.db.
.EXAMPLE
  powershell -File scripts/stop-api.ps1
#>
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$ApiDir = Join-Path $Root "services\api"
$dbPath = Join-Path $ApiDir "data\mywave_event.db"

function Stop-MyWaveApiProcesses {
  Write-Host "Stopping listeners on port 8000..." -ForegroundColor Yellow
  Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue |
    ForEach-Object {
      Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
      Write-Host "  killed port 8000 PID $($_.OwningProcess)"
    }

  Write-Host "Stopping uvicorn/python tied to MyWave Event App..." -ForegroundColor Yellow
  Get-CimInstance Win32_Process -Filter "name='python.exe'" -ErrorAction SilentlyContinue |
    ForEach-Object {
      $cmd = $_.CommandLine
      if (-not $cmd) { return }
      $isMyWave =
        ($cmd -match "app\.main:app") -and (
          ($cmd -match "127\.0\.0\.1.*8000") -or
          ($cmd -match "port 8000") -or
          ($cmd -match "mw_event_api_venv")
        )
      $isOrphanWorker = $cmd -match "multiprocessing\.spawn" -and $cmd -match "spawn_main"
      if ($isMyWave -or $isOrphanWorker) {
        Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
        Write-Host "  killed python PID $($_.ProcessId)"
      }
    }
}

function Test-DbUnlocked([string]$Path) {
  if (-not (Test-Path $Path)) { return $true }
  try {
    $fs = [IO.File]::Open($Path, "Open", "ReadWrite", "None")
    $fs.Close()
    return $true
  } catch {
    return $false
  }
}

Stop-MyWaveApiProcesses
Start-Sleep -Seconds 2

for ($i = 1; $i -le 5; $i++) {
  if (Test-DbUnlocked $dbPath) {
    Write-Host "DB unlocked: $dbPath" -ForegroundColor Green
    exit 0
  }
  Write-Host "DB still locked (attempt $i/5), waiting..." -ForegroundColor Yellow
  Stop-MyWaveApiProcesses
  Start-Sleep -Seconds 2
}

throw "DB still locked: $dbPath. Close API terminal windows (npm run dev), then run: powershell -File scripts/stop-api.ps1"

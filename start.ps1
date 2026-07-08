# Sagent startup script (Windows PowerShell)
param([switch]$NoFrontend)

$ErrorActionPreference = "Stop"
$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "=== Sagent Development Server ===" -ForegroundColor Cyan

# Start backend
Write-Host "Starting backend..." -ForegroundColor Yellow
$env:PYTHONPATH = "$RootDir\apps\agent-api\src;$RootDir\packages\tools\src;$RootDir\packages\agent-core\src;$RootDir\packages\memory\src"
$Backend = Start-Process -NoNewWindow -PassThru -FilePath "uv" -ArgumentList "run", "uvicorn", "sagent_agent_api.main:app", "--app-dir", "src", "--host", "127.0.0.1", "--port", "8765", "--reload" -WorkingDirectory "$RootDir\apps\agent-api"

Start-Sleep -Seconds 3

if (-not $NoFrontend) {
    Write-Host "Starting frontend..." -ForegroundColor Yellow
    $Frontend = Start-Process -NoNewWindow -PassThru -FilePath "pnpm" -ArgumentList "dev" -WorkingDirectory $RootDir
}

Write-Host "Backend: http://127.0.0.1:8765" -ForegroundColor Green
if (-not $NoFrontend) {
    Write-Host "Frontend: http://127.0.0.1:3000" -ForegroundColor Green
}

Write-Host "Press Ctrl+C to stop" -ForegroundColor Cyan

try {
    Wait-Process -Id $Backend.Id
}
finally {
    if ($Backend -and !$Backend.HasExited) { $Backend.Kill() }
    if ($Frontend -and !$Frontend.HasExited) { $Frontend.Kill() }
}

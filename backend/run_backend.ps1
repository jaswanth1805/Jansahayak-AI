# JanSahayak AI Backend Setup and Launcher Script
$BACKEND_DIR = $PSScriptRoot
$ROOT = Split-Path -Parent $BACKEND_DIR
$VENV_PYTHON = Join-Path $ROOT ".venv\Scripts\python.exe"
if (!(Test-Path $VENV_PYTHON)) {
    $SYSTEM_PYTHON = (Get-Command python -ErrorAction Stop).Source
    & $SYSTEM_PYTHON -m venv (Join-Path $ROOT ".venv")
    if ($LASTEXITCODE -ne 0) { throw "Could not create the project virtual environment." }
}
$PYTHON = $VENV_PYTHON

Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "   JanSahayak AI — Backend Launcher & Diagnostic     " -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan

Set-Location $BACKEND_DIR

Write-Host "`n[Step 1] Installing required packages..." -ForegroundColor Yellow
& $PYTHON -m pip install -r requirements.txt

Write-Host "`n[Step 2] Running backend verification test..." -ForegroundColor Yellow
& $PYTHON check_backend.py

Write-Host "`n[Step 3] Starting FastAPI Server on port 8000..." -ForegroundColor Green
& $PYTHON -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

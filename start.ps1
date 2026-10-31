# JanSahayak AI — Quick Start Script (PowerShell)
# Run this from the jansahayak-ai root directory

param(
    [switch]$SkipInstall,
    [switch]$BackendOnly,
    [switch]$FrontendOnly
)

$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
$BACKEND = Join-Path $ROOT "backend"
$FRONTEND = Join-Path $ROOT "frontend"
$PYTHON = "C:\Users\kanak\AppData\Local\Programs\Python\Python314\python.exe"

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "   JanSahayak AI - Quick Start  " -ForegroundColor Cyan  
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check .env file
$envFile = Join-Path $BACKEND ".env"
if (!(Test-Path $envFile)) {
    Write-Host "WARNING: backend/.env not found. Copying from .env.example..." -ForegroundColor Yellow
    Copy-Item (Join-Path $BACKEND ".env.example") $envFile
    Write-Host "Please edit backend/.env and add your OPENAI_API_KEY" -ForegroundColor Red
}

$envContent = Get-Content $envFile -Raw
if ($envContent -match "your_openai_api_key_here") {
    Write-Host ""
    Write-Host "⚠️  WARNING: OPENAI_API_KEY not configured in backend/.env" -ForegroundColor Yellow
    Write-Host "   AI features will not work without a valid OpenAI API key." -ForegroundColor Yellow
    Write-Host "   Get your key at: https://platform.openai.com/api-keys" -ForegroundColor Yellow
    Write-Host "   Then edit: $envFile" -ForegroundColor Yellow
    Write-Host ""
}

# Install backend dependencies
if (!$SkipInstall -and !$FrontendOnly) {
    Write-Host "Installing Python dependencies..." -ForegroundColor Green
    & $PYTHON -m pip install -r (Join-Path $BACKEND "requirements.txt") --quiet
    Write-Host "Python dependencies installed." -ForegroundColor Green
}

# Install frontend dependencies
if (!$SkipInstall -and !$BackendOnly) {
    Write-Host "Installing npm dependencies..." -ForegroundColor Green
    Push-Location $FRONTEND
    npm install --legacy-peer-deps --silent
    Pop-Location
    Write-Host "npm dependencies installed." -ForegroundColor Green
}

Write-Host ""
Write-Host "Starting servers..." -ForegroundColor Green
Write-Host ""

# Start backend
if (!$FrontendOnly) {
    Write-Host "▶ Backend: http://localhost:8000" -ForegroundColor Cyan
    Write-Host "  API Docs: http://localhost:8000/docs" -ForegroundColor Gray
    Start-Process powershell -ArgumentList @(
        "-NoExit",
        "-Command",
        "cd '$BACKEND'; & '$PYTHON' -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
    ) -WindowStyle Normal
    Start-Sleep -Seconds 3
}

# Start frontend
if (!$BackendOnly) {
    Write-Host "▶ Frontend: http://localhost:3000" -ForegroundColor Cyan
    Start-Process powershell -ArgumentList @(
        "-NoExit",
        "-Command",
        "cd '$FRONTEND'; npm run dev"
    ) -WindowStyle Normal
}

Write-Host ""
Write-Host "================================" -ForegroundColor Green
Write-Host " JanSahayak AI is starting up!  " -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""
Write-Host "Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "Backend:  http://localhost:8000" -ForegroundColor White
Write-Host "API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C or close the terminal windows to stop." -ForegroundColor Gray

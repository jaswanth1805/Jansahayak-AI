# JanSahayak AI Backend Setup and Launcher Script
$PYTHON = "C:\Users\kanak\AppData\Local\Programs\Python\Python314\python.exe"
$BACKEND_DIR = "C:\Users\kanak\.gemini\antigravity\scratch\jansahayak-ai\backend"

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

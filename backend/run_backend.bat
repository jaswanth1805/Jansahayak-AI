@echo off
set PYTHON=C:\Users\kanak\AppData\Local\Programs\Python\Python314\python.exe
cd /d "C:\Users\kanak\.gemini\antigravity\scratch\jansahayak-ai\backend"

echo ======================================================
echo    JanSahayak AI -- Backend Launcher
echo ======================================================

echo.
echo [Step 1] Installing / Verifying requirements...
"%PYTHON%" -m pip install -r requirements.txt

echo.
echo [Step 2] Verifying module imports...
"%PYTHON%" check_backend.py

echo.
echo [Step 3] Starting FastAPI Server...
"%PYTHON%" -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
pause

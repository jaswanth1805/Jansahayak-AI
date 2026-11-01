@echo off
set ROOT=%~dp0..
set VENV_PYTHON=%ROOT%\.venv\Scripts\python.exe
if not exist "%VENV_PYTHON%" (
    python -m venv "%ROOT%\.venv"
    if errorlevel 1 exit /b 1
)
set PYTHON=%VENV_PYTHON%
cd /d "%~dp0"

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

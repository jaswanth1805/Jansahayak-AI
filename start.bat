@echo off
echo.
echo ================================
echo    JanSahayak AI - Quick Start  
echo ================================
echo.

set ROOT=%~dp0
set BACKEND=%ROOT%backend
set FRONTEND=%ROOT%frontend
set PYTHON=%ROOT%\.venv\Scripts\python.exe

if not exist "%PYTHON%" (
    python -m venv "%ROOT%\.venv"
    if errorlevel 1 exit /b 1
)

echo Checking environment...

if not exist "%BACKEND%\.env" (
    echo Copying .env.example to .env...
    copy "%BACKEND%\.env.example" "%BACKEND%\.env"
    echo Please edit backend\.env and add your OPENAI_API_KEY
    pause
)

echo Installing backend dependencies...
"%PYTHON%" -m pip install -r "%BACKEND%\requirements.txt"
if errorlevel 1 exit /b 1

if not exist "%FRONTEND%\node_modules" (
    echo Installing frontend dependencies...
    pushd "%FRONTEND%"
    npm install --legacy-peer-deps
    if errorlevel 1 (popd & exit /b 1)
    popd
)

echo.
echo Starting Backend on http://localhost:8000 ...
start "JanSahayak Backend" cmd /k "cd /d "%BACKEND%" && "%PYTHON%" -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

timeout /t 3 /nobreak >nul

echo Starting Frontend on http://localhost:3000 ...
start "JanSahayak Frontend" cmd /k "cd /d "%FRONTEND%" && npm run dev"

echo.
echo ================================
echo  Both servers are starting up!
echo ================================
echo.
echo Frontend: http://localhost:3000
echo Backend:  http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
echo Close the opened terminal windows to stop.
pause

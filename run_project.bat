@echo off
echo ===================================================
echo Traffic Vision AI - NextGen Setup ^& Run Script
echo ===================================================

cd /d "%~dp0"

echo [1/3] Installing Backend Requirements (FastAPI)...
pip install -r backend\requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo Error installing python requirements.
    pause
    exit /b
)

echo [2/3] Installing Frontend Requirements (React / Vite)...
cd frontend
call npm install --legacy-peer-deps
if %ERRORLEVEL% NEQ 0 (
    echo Error installing Node modules.
    pause
    exit /b
)
cd ..

echo [3/3] Launching Application (Frontend ^& Backend)...
echo.
echo Application API will be available at http://localhost:8000
echo Application UI will be available at http://localhost:5173
echo.

start "Traffic Vision Backend (FastAPI)" cmd /c "uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"
start "Traffic Vision Frontend (React)" cmd /c "cd frontend && npm run dev"

echo Services have been started in separate windows.
pause

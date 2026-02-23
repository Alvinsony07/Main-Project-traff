@echo off
echo ===================================================
echo Traffic Vision AI - Setup & Run Script
echo ===================================================

cd /d "%~dp0"

echo [1/4] Installing requirements...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo Error installing requirements. Please check your python installation.
    pause
    exit /b
)

echo [2/4] Initializing Database & Admin User...
set FLASK_APP=app.py
flask create-admin

echo [3/4] Seeding Demo Data (for Analytics)...
python seed.py

echo [4/4] Launching Application...
echo.
echo Application will be available at http://localhost:5000
echo Login with username: admin / password: admin123
echo.
python app.py

pause

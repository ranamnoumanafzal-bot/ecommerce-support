@echo off
title Ecommerce Support Agent Launcher
echo Checking dependencies...

:: Try to import fastapi to see if requirements are installed
python -c "import fastapi, openai, uvicorn" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Installing missing Python packages...
    python -m pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install requirements. Please run: python -m pip install -r requirements.txt manually.
        pause
        exit /b
    )
)

echo Initializing database...
python init_db.py

echo Starting backend (this will open in a new window)...
:: 'start' first quoted string is the title. 
start "Ecom-Backend" cmd /k "python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000"

echo Opening the chat interface...
:: Wait a few seconds for server to boot
timeout /t 3 /nobreak
start explorer "frontend\index.html"

echo ========================================
echo ALL DONE!
echo If the chat doesn't work, check the backend window.
echo ========================================
pause
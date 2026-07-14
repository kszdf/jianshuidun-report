@echo off
title JianShuiDun Report System
color 0A

echo.
echo ========================================
echo   JianShuiDun Report System
echo   Quick Start (Windows)
echo ========================================
echo.

cd /d "%~dp0backend"

REM Check Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    echo Please install Python 3.10+ and check "Add to PATH"
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [OK] Python installed
python --version

REM Create venv if not exists
if not exist "venv" (
    echo.
    echo [*] First run: creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
)

REM Activate venv
call venv\Scripts\activate.bat

REM Install dependencies if needed
python -c "import fastapi" >nul 2>nul
if %errorlevel% neq 0 (
    echo.
    echo [*] Installing dependencies (first run, please wait)...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install dependencies
        pause
        exit /b 1
    )
    echo [OK] Dependencies installed
)

REM Init database if needed
if not exist "data\jianzao.db" (
    echo.
    echo [*] Initializing database with demo data...
    if not exist "data" mkdir data
    python init_data.py
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to initialize database
        pause
        exit /b 1
    )
    echo [OK] Database initialized
)

echo.
echo ========================================
echo   Server starting...
echo   URL: http://localhost:8000
echo   API Docs: http://localhost:8000/docs
echo   Demo: boss / 123456
echo   Press Ctrl+C to stop
echo ========================================
echo.

uvicorn main:app --host 0.0.0.0 --port 8000

pause

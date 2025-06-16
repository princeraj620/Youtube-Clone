@echo off
title YouTube Clone - Starting...
echo.
echo ========================================
echo    🎉 YouTube Clone Startup Script
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

echo ✅ Python found!
echo.

REM Check if virtual environment exists
if exist "venv\Scripts\activate.bat" (
    echo 🔄 Activating virtual environment...
    call venv\Scripts\activate.bat
    echo ✅ Virtual environment activated!
) else (
    echo 📦 Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo ✅ Virtual environment created and activated!
)

echo.
echo 📦 Installing/Checking dependencies...
pip install -r requirements.txt

echo.
echo 🚀 Starting YouTube Clone...
echo.
echo ========================================
echo    🌐 Access the website at:
echo    http://localhost:5000
echo.
echo    👤 Quick Demo Login:
echo    http://localhost:5000/demo-login
echo.
echo    🔑 Demo Credentials:
echo    Username: demo_user1
echo    Password: password123
echo ========================================
echo.

REM Start the application
python app.py

echo.
echo 👋 YouTube Clone stopped. Press any key to exit...
pause >nul 
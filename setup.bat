@echo off
echo ========================================
echo  Uber FirstGear - Quick Setup Script
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed!
    echo Please install Python 3.10+ from https://www.python.org/
    pause
    exit /b 1
)

echo [OK] Python is installed
echo.

REM Check if .env exists
if not exist ".env" (
    echo [WARNING] .env file not found!
    echo.
    echo Creating .env from template...
    if exist ".env.example" (
        copy .env.example .env
        echo [CREATED] .env file created from template
        echo.
        echo ========================================
        echo  ACTION REQUIRED:
        echo ========================================
        echo 1. Open the .env file
        echo 2. Replace YOUR_PASSWORD_HERE with your PostgreSQL password
        echo 3. Save the file
        echo 4. Run this script again
        echo.
        notepad .env
        pause
        exit /b 0
    ) else (
        echo [ERROR] .env.example template not found!
        echo Please create .env manually with:
        echo DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/uberclon
        pause
        exit /b 1
    )
)

echo [OK] .env file exists
echo.

REM Install dependencies
echo [STEP 1/3] Installing Python packages...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install packages
    pause
    exit /b 1
)
echo [OK] Packages installed
echo.

REM Setup database
echo [STEP 2/3] Setting up database tables...
python setup_database.py
if errorlevel 1 (
    echo [ERROR] Database setup failed
    echo.
    echo Common issues:
    echo - PostgreSQL is not running
    echo - Wrong password in .env file
    echo - Database 'uberclon' does not exist
    echo.
    echo To create database, run in psql:
    echo   CREATE DATABASE uberclon;
    echo.
    pause
    exit /b 1
)
echo [OK] Database tables created
echo.

REM Create sample data
echo [STEP 3/3] Creating test users...
python create_sample_data.py
if errorlevel 1 (
    echo [WARNING] Sample data creation failed
    echo This might be okay if data already exists
)
echo [OK] Test users created
echo.

echo ========================================
echo  Setup Complete! 
echo ========================================
echo.
echo To start the application:
echo   1. Open terminal and run: cd server && python run.py
echo   2. Open browser: http://localhost:8000/driver.html
echo.
echo Test Credentials:
echo   Driver: driver4 / password
echo   Rider:  rider6 / password
echo.
pause

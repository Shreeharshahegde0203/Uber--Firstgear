@echo off
echo ========================================
echo Starting Multiple Client Instances
echo ========================================
echo.
echo Opening browser tabs for testing...
echo.
echo Driver 1: http://localhost:8000 (driver.html)
start "" "http://localhost:8000/driver.html"
timeout /t 1 /nobreak >nul

echo Driver 2: http://localhost:8000 (driver.html)
start "" "http://localhost:8000/driver.html"
timeout /t 1 /nobreak >nul

echo Rider 1: http://localhost:8000 (index.html)
start "" "http://localhost:8000/index.html"
timeout /t 1 /nobreak >nul

echo Rider 2: http://localhost:8000 (index.html)
start "" "http://localhost:8000/index.html"
timeout /t 1 /nobreak >nul

echo.
echo ========================================
echo 4 browser tabs opened successfully!
echo ========================================
echo.
echo TESTING GUIDE:
echo 1. In Driver tabs: Go Online
echo 2. In Rider tabs: Login and Request Rides
echo 3. Watch automatic matching happen!
echo.
echo Press any key to exit...
pause >nul

@echo off
echo ========================================
echo  SmartPatch Quick Demo
echo ========================================
echo.

cd /d "%~dp0backend"

echo Starting Backend Server...
start "SmartPatch Backend" cmd /k "venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

echo Waiting for server to start...
timeout /t 4 /nobreak >nul

echo.
echo ========================================
echo  Backend Ready: http://localhost:8000
echo  Swagger Docs:  http://localhost:8000/docs
echo ========================================
echo.
echo Opening Simple HTML Demo...
timeout /t 1 /nobreak >nul

start "" "%~dp0frontend\simple.html"

echo.
echo Demo opened in your browser!
echo To stop the server, close the backend terminal window.
echo.
pause

@echo off
echo ========================================
echo  Starting SmartPatch Backend + Frontend
echo ========================================
echo.

cd /d "%~dp0backend"

echo [1/2] Starting Backend Server (port 8000)...
start "SmartPatch Backend" cmd /k "venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

timeout /t 3 /nobreak >nul

echo [2/2] Starting Frontend Server (port 5173)...
cd ..\frontend
start "SmartPatch Frontend" cmd /k "npm run dev"

echo.
echo ========================================
echo  Servers Started!
echo ========================================
echo  Backend:  http://localhost:8000
echo  Frontend: http://localhost:5173
echo  Swagger:  http://localhost:8000/docs
echo  Simple:   file:///%~dp0frontend\simple.html
echo ========================================
echo.
echo Press any key to open the frontend...
pause >nul

start http://localhost:5173

echo.
echo To stop servers, close the terminal windows.

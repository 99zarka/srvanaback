@echo off
echo Getting your network IP address...
for /f "tokens=2 delims=[]" %%a in ('ping -4 -n 1 %ComputerName% ^| find "Pinging"') do set IP=%%a
echo Found IP address: %IP%
echo.
echo Setting DJANGO_PRODUCTION=True...
set DJANGO_PRODUCTION=True
echo.
echo Starting Django server on %IP%:8000...
start cmd /k "cd /d %~dp0 && venv\Scripts\activate && set DJANGO_PRODUCTION=True && python manage.py runserver 0.0.0.0:8000"
echo.
echo Waiting for server to start...
timeout /t 3 >nul
echo.
echo Exposing backend with SSH tunnel using IP: %IP%
ssh -R 80:%IP%:8000 serveo.net

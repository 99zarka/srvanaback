@echo off
call .\venv\Scripts\activate.bat
echo Populating User Types...
python manage.py populate_user_types
echo.

echo Populating Services...
python manage.py populate_services
echo.

echo Data population complete.
pause

@echo off
call .\venv\Scripts\activate.bat
python manage.py test api.test_api_crud --verbosity 2 --noinput --keepdb
pause
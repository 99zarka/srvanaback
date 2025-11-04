@echo off
call .\venv\Scripts\activate.bat
python manage.py test api.tests.test_api --verbosity 2 --noinput --keepdb --parallel 10
pause

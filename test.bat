@echo off
call .\venv\Scripts\activate.bat
python manage.py test api.tests.test_models --verbosity 2 --noinput --keepdb
pause
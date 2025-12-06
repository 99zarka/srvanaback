@echo off
call .\venv\Scripts\activate.bat
python manage.py test  --verbosity 2 --noinput --keepdb  --settings=srvana.test_settings

pause

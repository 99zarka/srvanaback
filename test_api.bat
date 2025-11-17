@echo off
call .\venv\Scripts\activate.bat
python manage.py test  --verbosity 2 --noinput --keepdb --parallel auto
pause

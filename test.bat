@echo off
call .\venv\Scripts\activate
python manage.py test api --verbosity 2

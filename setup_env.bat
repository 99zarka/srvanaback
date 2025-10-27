@echo off
echo Checking for existing virtual environment...
if exist venv (
    echo Virtual environment already exists. Using existing venv.
) else (
    echo Creating virtual environment...
    python -m venv venv
)

if exist venv\Scripts\activate (
    echo Activating virtual environment...
    call venv\Scripts\activate
    echo Installing dependencies...
    pip install -r requirements.txt
    echo Virtual environment setup complete.
    echo Starting Django development server...
    python manage.py runserver
) else (
    echo Error: Virtual environment activation script not found.
    echo Please check if Python is installed correctly and accessible in your PATH.
)
pause

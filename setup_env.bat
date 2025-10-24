@echo off
echo Checking for existing virtual environment...
if exist venv (
    echo Removing existing virtual environment...
    rmdir /s /q venv
)

echo Creating virtual environment...
python -m venv venv

if exist venv\Scripts\activate (
    echo Activating virtual environment...
    call venv\Scripts\activate
    echo Installing dependencies...
    pip install -r requirements.txt
    echo Virtual environment setup complete.
) else (
    echo Error: Virtual environment activation script not found.
    echo Please check if Python is installed correctly and accessible in your PATH.
)
pause

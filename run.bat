@echo off
setlocal

echo ======================================
echo   SenioCare - Tool Calling Demo
echo ======================================

REM 1) Create venv if not exists
if not exist venv (
  echo [1/4] Creating virtual environment...
  python -m venv venv
)

REM 2) Activate venv
echo [2/4] Activating virtual environment...
call venv\Scripts\activate.bat

REM 3) Install dependencies
echo [3/4] Installing requirements...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

REM 4) Run the app
echo [4/4] Running SenioCare chat...
python ollama_integration.py

echo.
echo Finished. Press any key to close.
pause >nul
endlocal

@echo off
setlocal enabledelayedexpansion
title AI Dashboard - Startup
cd /d "%~dp0"

echo ============================================================
echo   AI Dashboard - Startup Script (Windows)
echo ============================================================
echo.

REM ------------------------------------------------------------
REM 1. Verify Python is installed
REM ------------------------------------------------------------
echo [1/6] Checking for Python...
where python >nul 2>nul
if %errorlevel% neq 0 (
    where python3 >nul 2>nul
    if %errorlevel% neq 0 (
        echo.
        echo [ERROR] Python was not found on this computer.
        echo Please install Python 3.12 or newer from:
        echo   https://www.python.org/downloads/
        echo IMPORTANT: On the first install screen, check the box
        echo that says "Add python.exe to PATH" before installing.
        echo.
        pause
        exit /b 1
    ) else (
        set "PYTHON_CMD=python3"
    )
) else (
    set "PYTHON_CMD=python"
)
echo       Found Python: !PYTHON_CMD!
for /f "tokens=*" %%v in ('!PYTHON_CMD! --version') do echo       Version: %%v
echo.

REM ------------------------------------------------------------
REM 2. Create virtual environment if it doesn't exist
REM ------------------------------------------------------------
echo [2/6] Checking virtual environment...
if not exist "venv\Scripts\activate.bat" (
    echo       No virtual environment found. Creating one now...
    !PYTHON_CMD! -m venv venv
    if !errorlevel! neq 0 (
        echo.
        echo [ERROR] Failed to create the virtual environment.
        echo Try running this script again, or see INSTRUCTION.md.
        echo.
        pause
        exit /b 1
    )
    echo       Virtual environment created successfully.
) else (
    echo       Virtual environment already exists.
)
echo.

REM ------------------------------------------------------------
REM 3. Activate the virtual environment
REM ------------------------------------------------------------
echo [3/6] Activating virtual environment...
call "venv\Scripts\activate.bat"
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to activate the virtual environment.
    echo.
    pause
    exit /b 1
)
echo       Virtual environment activated.
echo.

REM ------------------------------------------------------------
REM 4. Install missing dependencies
REM ------------------------------------------------------------
echo [4/6] Checking dependencies (this may take a minute the first time)...
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to install dependencies from requirements.txt.
    echo Check your internet connection and try again.
    echo.
    pause
    exit /b 1
)
echo       Dependencies are installed and up to date.
echo.

REM ------------------------------------------------------------
REM 5. Verify the .env file exists
REM ------------------------------------------------------------
echo [5/6] Checking configuration file (.env)...
if not exist ".env" (
    if exist ".env.example" (
        echo       No .env file found. Creating one from .env.example...
        copy /y ".env.example" ".env" >nul
        echo.
        echo       A new .env file was created for you.
        echo       IMPORTANT: Open .env in a text editor and add your
        echo       OPENAI_API_KEY to enable the AI Chat and Playground
        echo       features. See INSTRUCTION.md for step-by-step help.
        echo.
    ) else (
        echo       [WARNING] No .env or .env.example file found.
        echo       The app may not start correctly without one.
    )
) else (
    echo       .env file found.
    findstr /C:"OPENAI_API_KEY=sk-your" ".env" >nul 2>nul
    if !errorlevel! equ 0 (
        echo       [NOTICE] OPENAI_API_KEY still looks like the placeholder value.
        echo       AI features will be disabled until you add a real key.
        echo       See INSTRUCTION.md, section 12, for help.
    )
)
echo.

REM ------------------------------------------------------------
REM 6. Launch the application
REM ------------------------------------------------------------
echo [6/6] Starting AI Dashboard...
echo.
echo ============================================================
echo   The app will open at:  http://127.0.0.1:5000
echo   Keep this window open while using the app.
echo   Press CTRL+C in this window to stop the server.
echo ============================================================
echo.

start "" "http://127.0.0.1:5000"
python app.py

REM ------------------------------------------------------------
REM If the app exits or crashes, keep the window open so the
REM user can read any error messages instead of it vanishing.
REM ------------------------------------------------------------
echo.
echo ============================================================
echo   The application has stopped.
echo   If this was unexpected, scroll up to read any error
echo   messages above, or check the Troubleshooting section of
echo   INSTRUCTION.md.
echo ============================================================
pause

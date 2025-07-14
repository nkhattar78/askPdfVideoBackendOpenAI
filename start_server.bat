@echo off
REM Startup script for PDF and YouTube Video Query API
REM This script activates the virtual environment and starts the FastAPI server

echo 🚀 Starting PDF and YouTube Video Query API...
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo ❌ Virtual environment not found!
    echo Please create it first:
    echo    python -m venv venv
    echo    .\venv\Scripts\activate
    echo    pip install -r requirements.txt
    pause
    exit /b 1
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call .\venv\Scripts\activate

REM Check requirements
echo 🔍 Checking requirements...
python check_requirements.py
if errorlevel 1 (
    echo.
    echo ❌ Requirements check failed!
    pause
    exit /b 1
)

echo.
echo ✅ All requirements satisfied!
echo 🌐 Starting FastAPI server...
echo.
echo Available at:
echo   - Main API: http://localhost:8000
echo   - Interactive docs: http://localhost:8000/docs
echo   - Alternative docs: http://localhost:8000/redoc
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

echo.
echo 👋 Server stopped.
pause

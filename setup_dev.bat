@echo off
REM Development setup script for PDF and YouTube Video Query API
REM This script sets up the entire development environment

echo 🛠️  Setting up PDF and YouTube Video Query API Development Environment
echo ============================================================================
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH!
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo ✅ Python found: 
python --version

REM Create virtual environment
echo.
echo 📦 Creating virtual environment...
if exist "venv" (
    echo ⚠️  Virtual environment already exists. Skipping creation.
) else (
    python -m venv venv
    if errorlevel 1 (
        echo ❌ Failed to create virtual environment!
        pause
        exit /b 1
    )
    echo ✅ Virtual environment created successfully!
)

REM Activate virtual environment
echo.
echo 🔧 Activating virtual environment...
call .\venv\Scripts\activate

REM Upgrade pip
echo.
echo 📈 Upgrading pip...
python -m pip install --upgrade pip

REM Install requirements
echo.
echo 📚 Installing requirements...
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ Failed to install requirements!
    pause
    exit /b 1
)

REM Verify installation
echo.
echo 🔍 Verifying installation...
python check_requirements.py

REM Check environment file
echo.
echo 📋 Checking environment configuration...
if exist ".env" (
    echo ✅ Found .env file
) else (
    echo ⚠️  No .env file found. Creating template...
    echo SHREYA_NAME="Your Name" > .env
    echo. >> .env
    echo # Qdrant Configuration >> .env
    echo QDRANT_KEY = "your-qdrant-api-key" >> .env
    echo. >> .env
    echo # Azure OpenAI Configuration >> .env
    echo AZURE_OPENAI_API_KEY = "your-azure-openai-api-key" >> .env
    echo AZURE_OPENAI_ENDPOINT = "https://your-resource-name.openai.azure.com/" >> .env
    echo AZURE_OPENAI_DEPLOYMENT_NAME = "your-gpt-deployment-name" >> .env
    echo AZURE_OPENAI_API_VERSION = "2025-01-01-preview" >> .env
    echo.
    echo 📝 Template .env file created. Please update it with your actual credentials.
)

echo.
echo ============================================================================
echo 🎉 Setup Complete!
echo ============================================================================
echo.
echo Next steps:
echo 1. Update .env file with your Azure OpenAI and Qdrant credentials
echo 2. Start the server: start_server.bat
echo 3. Or run manually: uvicorn app.main:app --reload
echo 4. Test the API: python test_api.py
echo.
echo 📚 Documentation: README.md
echo 🌐 API docs: http://localhost:8000/docs (after starting server)
echo.
pause

@echo off
echo ==========================================
echo    Claude Chat UI - Ollama Edition
echo ==========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed! Please install Python 3.8+ first.
    pause
    exit /b 1
)

REM Install dependencies if needed
echo Checking dependencies...
python -c "import flask, requests" 2>nul
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
)

REM Check if Ollama is running
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo.
    echo ==========================================
    echo    OLLAMA NOT DETECTED!
    echo ==========================================
    echo.
    echo Ollama doesn't seem to be running.
    echo.
    echo To set up Ollama:
    echo   1. Install from: https://ollama.com
    echo   2. Open a new terminal and run: ollama serve
    echo   3. Pull a model: ollama pull llama3.2
    echo.
    echo Then run this script again.
    echo.
    pause
    exit /b 1
)

echo.
echo Ollama detected! Starting Claude Chat UI...
echo Open http://localhost:5000 in your browser
echo.

python app.py

pause

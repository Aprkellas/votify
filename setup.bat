@echo off
echo ============================================================
echo   Votify Setup
echo ============================================================
echo.

REM Check Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found.
    echo Please install Python 3.8+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during install.
    pause
    exit /b 1
)

echo [1/3] Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment.
    pause
    exit /b 1
)

echo [2/3] Installing dependencies...
call venv\Scripts\activate
pip install --upgrade pip --quiet
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies.
    pause
    exit /b 1
)

echo [3/3] Verifying FFmpeg (auto-downloaded on first run)...
python -c "import static_ffmpeg; static_ffmpeg.add_paths(); print('FFmpeg ready.')"

echo.
echo ============================================================
echo   Setup complete!
echo ============================================================
echo.
echo To use Votify:
echo   1. Activate the environment:   venv\Scripts\activate
echo   2. Run:   python votify.py ^<spotify_url^>
echo.
echo No credentials needed -- just paste any Spotify link.
echo.
pause

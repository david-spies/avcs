@echo off
:: AVCS - Audio Video Conversion Suite
:: Windows launcher

title AVCS - Audio Video Conversion Suite

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found.
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

:: Check PyQt5
python -c "import PyQt5" >nul 2>&1
if errorlevel 1 (
    echo Installing PyQt5...
    pip install PyQt5
)

:: Check ffmpeg
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo [WARNING] ffmpeg not found on PATH.
    echo Download from https://ffmpeg.org/download.html
    echo AVCS will launch but conversion will be unavailable.
    echo.
)

:: Launch AVCS
echo Starting AVCS...
python "%~dp0main.py"

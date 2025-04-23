@echo off
echo ============================
echo Building with Nuitka...
echo ============================

REM Set your script name and icon
set SCRIPT_NAME=frame_extractor_gui.py
set ICON=icon.ico

REM Make sure Nuitka is installed
where nuitka >nul 2>nul
if errorlevel 1 (
    echo Nuitka is not installed. Installing now...
    pip install nuitka wheel
)

REM Compile the script
python -m nuitka ^
    --standalone ^
    --enable-plugin=tk-inter ^
    --windows-icon-from-ico=%ICON% ^
    --output-dir=build ^
    --remove-output ^
    --show-progress ^
    --show-memory ^
    %SCRIPT_NAME%

echo.
echo ✅ Build complete! Your EXE is in the "build" folder.
pause

@echo off
setlocal
set "CHROME_FOUND="

echo ============================================
echo   Ozon Price Tracker Bot - Installation
echo ============================================
echo.

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
    if %ERRORLEVEL% neq 0 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
) else (
    echo Virtual environment already exists, reusing it...
)

echo Activating virtual environment...
call venv\Scripts\activate.bat
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

echo Upgrading pip...
python -m pip install --upgrade pip
if %ERRORLEVEL% neq 0 (
    echo WARNING: Failed to upgrade pip, continuing...
)

echo Installing Python dependencies...
pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to install Python dependencies
    pause
    exit /b 1
)

echo Installing Playwright browsers...
playwright install chromium
if %ERRORLEVEL% neq 0 (
    echo WARNING: Failed to install Playwright browsers
)

echo Checking browser availability for Selenium...
where chrome >nul 2>&1 && set "CHROME_FOUND=1"
where msedge >nul 2>&1 && set "CHROME_FOUND=1"
where chromium >nul 2>&1 && set "CHROME_FOUND=1"

if not defined CHROME_FOUND if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" set "CHROME_FOUND=1"
if not defined CHROME_FOUND if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" set "CHROME_FOUND=1"
if not defined CHROME_FOUND if exist "%LocalAppData%\Google\Chrome\Application\chrome.exe" set "CHROME_FOUND=1"
if not defined CHROME_FOUND if exist "%ProgramFiles%\Microsoft\Edge\Application\msedge.exe" set "CHROME_FOUND=1"
if not defined CHROME_FOUND if exist "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" set "CHROME_FOUND=1"

if defined CHROME_FOUND (
    echo Browser for Selenium: OK
) else (
    echo WARNING: Chrome/Chromium/Edge was not found on this system.
    echo Selenium package is installed, but browser-based cookie retrieval may not work
    echo until you install Google Chrome, Chromium, or Microsoft Edge.
)

if not exist config.txt (
    echo Creating config.txt from config.txt.example...
    copy /Y config.txt.example config.txt >nul
)

echo.
echo ============================================
echo   Installation completed successfully!
echo ============================================
echo.
echo Next steps:
echo 1. Open config.txt
echo 2. Fill BOT_TOKEN and other settings
echo 3. If you plan to use Selenium cookies, make sure Chrome/Chromium/Edge is installed
echo 4. Run the bot with: venv\Scripts\activate.bat ^&^& python main.py
echo.

pause

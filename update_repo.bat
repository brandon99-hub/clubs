@echo off
echo ========================================
echo    Django Project Auto-Update Script
echo ========================================
echo.

:: Change to the project directory
cd /d "%~dp0"

echo [INFO] Current directory: %CD%
echo [INFO] Starting repository update...
echo.

:: Check if git is available
git --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Git is not installed or not in PATH
    echo Please install Git and try again
    pause
    exit /b 1
)

:: Check if this is a git repository
git status >nul 2>&1
if errorlevel 1 (
    echo [ERROR] This is not a git repository
    echo Please make sure you're in the correct directory
    pause
    exit /b 1
)

echo [INFO] Fetching latest changes from remote repository...
git fetch origin

if errorlevel 1 (
    echo [ERROR] Failed to fetch from remote repository
    echo Please check your internet connection and try again
    pause
    exit /b 1
)

echo [SUCCESS] Fetched latest changes successfully
echo.

:: Check if there are any local changes
git status --porcelain | findstr /r "^[^?]" >nul
if not errorlevel 1 (
    echo [WARNING] You have local changes that might be overwritten
    echo.
    set /p choice="Do you want to stash your changes before pulling? (y/n): "
    if /i "%choice%"=="y" (
        echo [INFO] Stashing local changes...
        git stash
        if errorlevel 1 (
            echo [ERROR] Failed to stash changes
            pause
            exit /b 1
        )
        echo [SUCCESS] Changes stashed successfully
        set STASHED=1
    ) else (
        echo [INFO] Proceeding without stashing...
    )
    echo.
)

:: Pull the latest changes
echo [INFO] Pulling latest changes from remote repository...
git pull origin main

if errorlevel 1 (
    echo [ERROR] Failed to pull changes
    echo This might be due to conflicts or network issues
    echo.
    if defined STASHED (
        echo [INFO] Restoring stashed changes...
        git stash pop
    )
    pause
    exit /b 1
)

echo [SUCCESS] Successfully pulled latest changes
echo.

:: Restore stashed changes if any
if defined STASHED (
    echo [INFO] Restoring stashed changes...
    git stash pop
    if errorlevel 1 (
        echo [WARNING] There might be conflicts with stashed changes
        echo Please resolve them manually
    ) else (
        echo [SUCCESS] Stashed changes restored successfully
    )
    echo.
)

:: Show the latest commit info
echo [INFO] Latest commit information:
git log -1 --oneline
echo.

:: Check if there are any new dependencies
if exist "requirements.txt" (
    echo [INFO] Checking for new dependencies...
    echo [INFO] You may want to run: pip install -r requirements.txt
    echo.
)

:: Check if Django migrations are needed
echo [INFO] Checking for database migrations...
echo [INFO] You may want to run: python manage.py migrate
echo.

echo ========================================
echo    Update completed successfully!
echo ========================================
echo.
echo [INFO] Your local repository is now up to date
echo [INFO] Remember to restart your Django server if needed
echo.
pause 
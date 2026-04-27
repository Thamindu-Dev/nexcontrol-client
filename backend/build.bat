@echo off
echo ============================================================
echo  NexControl Server - Windows Build
echo ============================================================
echo.

REM Kill running instance if any
tasklist /FI "IMAGENAME eq NexControl.exe" 2>NUL | find /I "NexControl.exe" >NUL
if %ERRORLEVEL% equ 0 (
    echo [INFO] NexControl.exe is running. Stopping...
    taskkill /IM NexControl.exe /F >NUL 2>&1
    timeout /t 2 /nobreak >NUL
)

REM Remove old build artifacts
if exist "dist\NexControl.exe" del /F "dist\NexControl.exe"

pip install pyinstaller >nul 2>&1

pyinstaller --onefile --name NexControl ^
  --add-data "app;app" ^
  --hidden-import passlib ^
  --hidden-import passlib.handlers.argon2 ^
  --hidden-import argon2 ^
  --hidden-import win32crypt ^
  --hidden-import qrcode ^
  --hidden-import cryptography ^
  --hidden-import jose ^
  --hidden-import customtkinter ^
  --hidden-import PIL ^
  --hidden-import docker ^
  --hidden-import psutil ^
  --hidden-import pyautogui ^
  --hidden-import pystray ^
  --uac-admin ^
  --noconfirm ^
  main.py

echo.
if %ERRORLEVEL% equ 0 (
    if exist "dist\NexControl.exe" (
        echo [OK] Build successful: dist\NexControl.exe
    ) else (
        echo [FAIL] Build completed but exe not found
    )
) else (
    echo [FAIL] Build failed with error code %ERRORLEVEL%
)
pause

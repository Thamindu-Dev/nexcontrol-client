@echo off
echo ============================================================
echo  NexControl Server - Windows Build
echo ============================================================
echo.

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
if exist "dist\NexControl.exe" (
    echo [OK] Build successful: dist\NexControl.exe
) else (
    echo [FAIL] Build failed
)
pause

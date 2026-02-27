@echo off
title Adharsh Browser Auditor - Enterprise Build Script
echo ===================================================
echo   Adharsh Browser Auditor - Enterprise Build Script
echo ===================================================

echo [1/3] Installing dependencies...
pip install customtkinter Pillow PyInstaller

echo [2/3] Building Main Application...
pyinstaller --noconsole --onefile --name "Adharsh_Browser_Auditor" --icon="app_logo.ico" --collect-all customtkinter --add-data "app_logo.png;." --clean gui.py

echo [3/3] Building Professional Installer with Inno Setup...
"%LOCALAPPDATA%\Programs\Inno Setup 6\iscc.exe" installer_config.iss

echo ===================================================
echo [v] Build Successful! 
echo Final Installer: dist\Adharsh_Auditor_Setup_Windows.exe
echo ===================================================
pause

@echo off
title Adharsh Browser Auditor - Enterprise Build Script
echo ===================================================
echo   Adharsh Browser Auditor - Enterprise Build Script
echo ===================================================

echo [1/4] Installing dependencies...
pip install customtkinter Pillow PyInstaller

echo [2/4] Building Main Application...
pyinstaller --noconsole --onefile --name "Adharsh_Browser_Auditor" --icon="app_logo.ico" --collect-all customtkinter --add-data "app_logo.png;." --clean gui.py

echo [3/4] Building Setup Wizard...
:: Bundle the main EXE inside the Setup Wizard as a resource
pyinstaller --noconsole --onefile --name "Setup_Adharsh_Auditor" --icon="app_logo.ico" --collect-all customtkinter --add-data "app_logo.png;." --add-data "app_logo.ico;." --add-data "dist/Adharsh_Browser_Auditor.exe;." --clean setup_wizard.py

echo [4/4] Finalizing...
if exist dist\Setup_Adharsh_Auditor.exe (
    copy /Y "dist\Setup_Adharsh_Auditor.exe" "dist\Adharsh_Auditor_Setup_Windows.exe"
)

echo ===================================================
echo [v] Build Successful! 
echo Final Installer: dist\Adharsh_Auditor_Setup_Windows.exe
echo ===================================================
pause

@echo off
rem Double-click to install and run the EMPIRE Reply bot on this PC.
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup.ps1"
pause

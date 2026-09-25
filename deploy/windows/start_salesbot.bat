@echo off
rem Double-click to set up and run the WINTER ARC sales bot on this PC.
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0salesbot.ps1"
pause

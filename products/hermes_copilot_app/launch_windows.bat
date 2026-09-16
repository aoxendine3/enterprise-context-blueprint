@echo off
REM ==============================================================================
REM Hermes Copilot — Windows Production Launcher
REM Sovereign Local Executive Gateway (Port 8085)
REM ==============================================================================

title Hermes Copilot - Sovereign Gateway
echo ==================================================================
echo   HERMES COPILOT -- SOVEREIGN AGENT SUITE (WINDOWS x64)
echo ==================================================================

cd /d "%~dp0"

REM Check Ollama
echo [*] Checking Sovereign Local Inference Core (http://127.0.0.1:11434)...
curl -s http://127.0.0.1:11434/api/tags >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Notice: Ollama daemon not running. Embedded autonomous transformer will activate as fallback.
) else (
    echo [+] Ollama inference engine detected and online.
)

REM Voice dispatch
powershell -NoProfile -Command "Add-Type -AssemblyName System.speech; $s = New-Object System.Speech.Synthesis.SpeechSynthesizer; $s.SpeakAsync('Hermes Copilot sovereign gateway launching on port 8085.')" >nul 2>&1

echo [*] Booting Hermes Copilot Server on http://127.0.0.1:8085 ...
start http://127.0.0.1:8085/
python server.py
pause

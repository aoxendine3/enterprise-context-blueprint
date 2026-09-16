@echo off
echo ================================================
echo   XORAS Voice Pipeline - Sovereign Audio Input
echo ================================================
echo [Xoras] Starting voice capture daemon...
start /B python "%~dp0agents\voice\voice_capture.py"
timeout /t 2 /nobreak >nul
echo [Xoras] Starting voice router (STT + intent dispatch)...
start /B python "%~dp0agents\voice\voice_router.py"
echo [Xoras] Voice pipeline active. Speak to Maxx.
echo Press any key to exit (daemons continue in background)...
pause >nul

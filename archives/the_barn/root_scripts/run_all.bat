@echo off
echo ================================================================
echo   XORAS Sovereign Command OS -- Full System Boot
echo   All models powered by sovereign-hermes (local bare metal)
echo ================================================================
echo.
call "%~dp0run_store.bat"
call "%~dp0run_voice.bat"
echo.
echo [Xoras] All systems online. sovereign-hermes is your engine.
echo   Store:  http://127.0.0.1:8085/store.html
echo   Voice:  Active (microphone capture + STT + model dispatch)
echo   Ollama: http://127.0.0.1:11434
pause

@echo off
echo ================================================
echo   XORAS Sovereign Store Server - Port 8085
echo ================================================
start /B python "%~dp0products\xmars_os\server.py"
echo [Xoras] Store live at http://127.0.0.1:8085/store.html
echo Press any key to exit (server continues in background)...
pause >nul

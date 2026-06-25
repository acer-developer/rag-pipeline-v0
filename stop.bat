@echo off
echo Stopping Rag Pipeline V0...

taskkill /F /IM ngrok.exe >nul 2>&1
if %ERRORLEVEL%==0 (echo  - ngrok stopped) else (echo  - ngrok was not running)

powershell -NoProfile -Command "$p = Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { $_.CommandLine -like '*streamlit*' }; if ($p) { $p | ForEach-Object { Stop-Process -Id $_.ProcessId -Force; Write-Host ' - Streamlit stopped (PID ' $_.ProcessId ')' } } else { Write-Host ' - Streamlit was not running' }"

echo Done.
timeout /t 2 /nobreak >nul

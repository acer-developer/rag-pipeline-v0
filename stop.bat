@echo off
echo Stopping Rag Pipeline V0...

taskkill /F /IM ngrok.exe >nul 2>&1
if %ERRORLEVEL%==0 (echo  - ngrok stopped) else (echo  - ngrok was not running)

set "FOUND="
for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":8501 " ^| findstr "LISTENING"') do (
  taskkill /F /PID %%P >nul 2>&1
  echo  - Streamlit stopped ^(PID %%P^)
  set "FOUND=1"
)
if not defined FOUND echo  - Streamlit was not running on port 8501

echo Done.
timeout /t 2 /nobreak >nul

@echo off
title Rag Pipeline V0
pushd "%~dp0"

echo === Rag Pipeline V0 ===
echo Project: %CD%
echo.

if not exist ".venv\Scripts\python.exe" (
  echo [ERROR] .venv not found. Run setup first:
  echo   uv venv --python 3.11 .venv
  echo   uv pip install --python .venv -r requirements.txt
  pause
  exit /b 1
)

echo Checking for existing Streamlit / ngrok processes...
taskkill /F /IM ngrok.exe >nul 2>&1
for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":8501 " ^| findstr "LISTENING"') do (
  echo Killing existing process on port 8501 (PID %%P)
  taskkill /F /PID %%P >nul 2>&1
)

set "NGROK=%LOCALAPPDATA%\Microsoft\WinGet\Packages\Ngrok.Ngrok_Microsoft.Winget.Source_8wekyb3d8bbwe\ngrok.exe"

if exist "%NGROK%" (
  echo Starting ngrok in background...
  start "" /B "%NGROK%" http 8501 > "%TEMP%\ngrok.log" 2>&1
) else (
  echo [WARN] ngrok not found - public tunnel skipped.
)

echo Starting Streamlit (will take ~10 seconds to come up)...
echo.
echo  Local:  http://localhost:8501
echo  Public: https://donator-aged-enactment.ngrok-free.dev
echo.
echo Browser will open automatically once Streamlit is ready.
echo Closing this window stops everything.
echo ---------------------------------------------------------------

start "" /B cmd /c "ping 127.0.0.1 -n 12 >nul && start "" http://localhost:8501"

.venv\Scripts\python.exe -m streamlit run app.py

echo.
echo Streamlit exited. Cleaning up ngrok...
taskkill /F /IM ngrok.exe >nul 2>&1
popd
pause

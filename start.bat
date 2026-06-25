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

set "NGROK=%LOCALAPPDATA%\Microsoft\WinGet\Packages\Ngrok.Ngrok_Microsoft.Winget.Source_8wekyb3d8bbwe\ngrok.exe"

if exist "%NGROK%" (
  echo Starting ngrok tunnel in background...
  start "" /B "%NGROK%" http 8501 --log=stdout --log-format=json > "%TEMP%\ngrok.log" 2>&1
) else (
  echo [WARN] ngrok not found - skipping public tunnel.
)

echo Opening browser...
start "" "http://localhost:8501"

echo.
echo  Local:  http://localhost:8501
echo  Public: https://donator-aged-enactment.ngrok-free.dev
echo.
echo Streamlit will start now. Closing this window stops everything.
echo ---------------------------------------------------------------
echo.

.venv\Scripts\python.exe -m streamlit run app.py

echo.
echo Streamlit exited. Cleaning up ngrok...
taskkill /F /IM ngrok.exe >nul 2>&1
popd
pause

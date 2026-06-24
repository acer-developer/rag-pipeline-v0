@echo off
setlocal
cd /d "%~dp0"

echo Starting Rag Pipeline V0...
echo.

start "Streamlit" cmd /k ".venv\Scripts\python.exe -m streamlit run app.py"

timeout /t 5 /nobreak >nul

start "ngrok tunnel" cmd /k "%LOCALAPPDATA%\Microsoft\WinGet\Packages\Ngrok.Ngrok_Microsoft.Winget.Source_8wekyb3d8bbwe\ngrok.exe http 8501"

timeout /t 3 /nobreak >nul

start "" "http://localhost:8501"

echo.
echo Local:  http://localhost:8501
echo Public: https://donator-aged-enactment.ngrok-free.dev
echo.
echo Two windows opened (Streamlit + ngrok). Close them to stop.
pause

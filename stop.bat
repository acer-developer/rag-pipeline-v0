@echo off
echo Stopping Rag Pipeline V0...
taskkill /F /IM ngrok.exe 2>nul
taskkill /F /FI "WINDOWTITLE eq Streamlit*" 2>nul
taskkill /F /FI "WINDOWTITLE eq ngrok tunnel*" 2>nul
echo Done.
timeout /t 2 /nobreak >nul

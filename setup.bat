@echo off
title Rag Pipeline V0 - Setup
pushd "%~dp0"

echo === Rag Pipeline V0 - First-time setup ===
echo Project: %CD%
echo.

where uv >nul 2>&1
if errorlevel 1 (
  echo [ERROR] 'uv' is not installed. Install it with:
  echo   powershell -c "irm https://astral.sh/uv/install.ps1 ^| iex"
  echo Then re-run this script.
  pause
  exit /b 1
)

if exist ".venv\Scripts\python.exe" (
  echo Virtual env already exists at .venv - skipping create.
) else (
  echo Creating Python 3.11 venv...
  uv venv --python 3.11 .venv
  if errorlevel 1 ( echo [ERROR] venv create failed. & pause & exit /b 1 )
)

echo Installing Python dependencies...
uv pip install --python .venv -r requirements.txt
if errorlevel 1 ( echo [ERROR] pip install failed. & pause & exit /b 1 )

echo.
where ollama >nul 2>&1
if errorlevel 1 (
  echo [INFO] Ollama not found. Install it from https://ollama.com/download
  echo        Then run: ollama pull llama3.1:8b
) else (
  echo Ollama detected. Checking for llama3.1:8b...
  ollama list | findstr /C:"llama3.1:8b" >nul
  if errorlevel 1 (
    echo Pulling llama3.1:8b ^(~4.7 GB, one-time download^)...
    ollama pull llama3.1:8b
  ) else (
    echo  - llama3.1:8b already present.
  )
)

echo.
where ngrok >nul 2>&1
if errorlevel 1 (
  echo [INFO] ngrok not found. Public tunnel will be skipped.
  echo        To enable public URL: install ngrok from https://ngrok.com/download
  echo        Sign up free, then run: ngrok config add-authtoken ^<your-token^>
) else (
  echo  - ngrok detected.
)

echo.
if not exist ".env" (
  if exist ".env.example" (
    copy .env.example .env >nul
    echo Created .env from .env.example - edit it to add your Chroma Cloud keys.
  )
) else (
  echo  - .env already exists.
)

echo.
echo === Setup complete ===
echo.
echo Next:
echo  1. Edit .env and fill in CHROMA_API_KEY / CHROMA_TENANT / CHROMA_DATABASE
echo  2. Drop your PDF into data\
echo  3. Run: .venv\Scripts\python.exe ingest.py
echo  4. Then double-click start.bat
echo.
pause
popd

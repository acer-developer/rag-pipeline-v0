@echo off
title Rag Pipeline V0
pushd "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo [ERROR] .venv not found. Run setup first:
  echo   uv venv --python 3.11 .venv
  echo   uv pip install --python .venv -r requirements.txt
  pause
  exit /b 1
)

.venv\Scripts\python.exe launcher.py
popd
pause

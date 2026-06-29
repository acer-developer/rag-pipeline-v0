@echo off
title Rag Pipeline V0
pushd "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo [ERROR] .venv not found. Run setup.bat first.
  pause
  exit /b 1
)

.venv\Scripts\python.exe webapp\launcher.py
popd
pause

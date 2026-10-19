@echo off
cd /d "%~dp0"
if not exist .venv (
  echo First start: installing dependencies into .venv (one time)...
  py -3 -m venv .venv || python -m venv .venv
  .venv\Scripts\pip install -q -r requirements.txt
)
set PORT=%1
if "%PORT%"=="" set PORT=8120
.venv\Scripts\python serve.py %PORT%
pause

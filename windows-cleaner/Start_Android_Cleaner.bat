@echo off
setlocal
cd /d "%~dp0"
py -3 windows_cleaner.py
if errorlevel 1 (
  echo.
  echo Verifique se o Python 3 esta instalado e tente novamente.
  pause
)

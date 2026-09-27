@echo off
title API Sistema Academico
cd /d "%~dp0"
if not exist venv\Scripts\activate.bat (
    echo Primero ejecute INSTALAR_WINDOWS.bat
    pause
    exit /b 1
)
call venv\Scripts\activate.bat
python -m uvicorn main:app --reload
pause


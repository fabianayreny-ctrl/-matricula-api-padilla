@echo off
title Instalar API Sistema Academico
cd /d "%~dp0"
python -m venv venv
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
echo.
echo Instalacion completada. Ahora ejecute INICIAR_API_WINDOWS.bat
pause


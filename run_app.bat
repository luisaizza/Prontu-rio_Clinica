@echo off
title Sistema Clinica
color 0F

echo ========================================================
echo           INICIANDO SISTEMA CLINICA
echo ========================================================
echo.

REM Garante que estamos na pasta do arquivo .bat
cd /d "%~dp0"

echo [1/3] Ativando ambiente virtual...
call .venv\Scripts\activate.bat

echo [2/3] Abrindo navegador...
REM Espera 2 segundos para garantir que o Python comece a carregar
timeout /t 2 /nobreak >nul
start http://127.0.0.1:5000

echo [3/3] Iniciando servidor...
echo.
python app_clinica.py
pause
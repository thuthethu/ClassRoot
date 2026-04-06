@echo off
setlocal enabledelayedexpansion

echo =======================================================
echo LIMPANDO BUILDS ANTIGOS E PREPARANDO NOVA VERSAO
echo =======================================================
echo.

:: Garante que o terminal está rodando de dentro da pasta correta
cd /d "%~dp0"

:: Garante que o arquivo de mapa de fotos existe
if not exist mapa_fotos.json (
    echo {} > mapa_fotos.json
)

:: Garante que pastas essenciais existem
if not exist static mkdir static
if not exist static\fotos_alunos mkdir static\fotos_alunos
if not exist templates mkdir templates

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo Instalando dependencias necessarias...
pip install pyinstaller flask pandas openpyxl Pillow

echo.
echo Gerando o executavel ClassRoot...
echo Isso pode demorar 2-5 minutos.
pyinstaller run_app.py --clean --onefile --windowed --add-data "templates;templates" --add-data "static;static" --name ClassRoot --hidden-import jinja2 --hidden-import flask --exclude-module streamlit --exclude-module matplotlib

echo.
echo =======================================================
echo PRONTO! O executavel novo esta na pasta "dist".
echo Execute o "ClassRoot.exe" dentro da pasta "dist".
echo =======================================================
pause

@echo off
echo 🚀 QUICK START - WHISPER SERVER
echo ===============================

set "action=%1"
if "%action%"=="" set "action=help"

if "%action%"=="setup" goto :setup
if "%action%"=="dev" goto :dev
if "%action%"=="test" goto :test
if "%action%"=="docker" goto :docker
if "%action%"=="validate" goto :validate
if "%action%"=="clean" goto :clean
goto :help

:setup
echo 📦 Executando setup...
python scripts\setup_local.py
if errorlevel 1 (
    echo ❌ Erro no setup
    pause
    exit /b 1
)
echo ✅ Setup concluído!
echo 💡 Para ativar: venv\Scripts\activate
pause
exit /b 0

:dev
echo 🔥 Modo desenvolvimento...
if not exist "venv\Scripts\python.exe" (
    echo ❌ Virtual environment não encontrado
    echo 💡 Execute: quick_start.bat setup
    pause
    exit /b 1
)
echo 🚀 Iniciando servidor...
cd src
..\venv\Scripts\python.exe servidor_whisper.py
goto :end

:test
echo 🧪 Executando testes...
if not exist "venv\Scripts\python.exe" (
    echo ❌ Virtual environment não encontrado
    pause
    exit /b 1
)
echo 📋 1. Testes da API...
venv\Scripts\python.exe scripts\test_api.py
echo ✅ Testes concluídos!
pause
goto :end

:docker
echo 🐳 Executando via Docker...
echo 🔨 1. Build da imagem...
docker build -f docker\Dockerfile -t whisper-api .
if errorlevel 1 (
    echo ❌ Erro no build
    pause
    exit /b 1
)
echo 🚀 2. Executando container...
docker run -p 5555:5555 --name whisper-dev whisper-api
goto :end

:validate
echo 🔍 Validação pré-deploy...
if not exist "venv\Scripts\python.exe" (
    echo ❌ Virtual environment não encontrado
    pause
    exit /b 1
)
venv\Scripts\python.exe scripts\validate_deploy.py
pause
goto :end

:clean
echo 🧹 Limpando ambiente...
docker stop whisper-dev 2>nul
docker rm whisper-dev 2>nul
docker rmi whisper-api 2>nul
if exist "logs\*" del /q logs\*
echo ✅ Ambiente limpo!
pause
goto :end

:help
echo Uso: quick_start.bat [comando]
echo.
echo Comandos disponíveis:
echo   setup      - Setup completo do ambiente
echo   dev        - Executar em modo desenvolvimento
echo   test       - Executar testes da API
echo   docker     - Executar via Docker
echo   validate   - Validar antes do deploy
echo   clean      - Limpar ambiente
echo.
pause

:end 
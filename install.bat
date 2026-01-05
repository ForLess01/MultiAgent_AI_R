@echo off
REM =============================================================================
REM Script de instalación automática para Windows
REM =============================================================================

echo ================================================================================
echo  INSTALACION DEL SISTEMA MULTIAGENTE DE NOTICIAS
echo ================================================================================
echo.

REM Verificar Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python no esta instalado o no esta en el PATH
    echo Por favor instala Python 3.9 o superior desde https://www.python.org/
    pause
    exit /b 1
)

echo [OK] Python detectado
python --version
echo.

REM Crear entorno virtual (opcional pero recomendado)
echo ¿Deseas crear un entorno virtual? (Recomendado para evitar conflictos)
echo 1. Si
echo 2. No, usar Python global
choice /c 12 /n /m "Selecciona opcion (1 o 2): "

if %errorlevel%==1 (
    echo.
    echo [*] Creando entorno virtual...
    python -m venv venv
    
    echo [*] Activando entorno virtual...
    call venv\Scripts\activate.bat
    
    echo [OK] Entorno virtual activado
)

echo.
echo [*] Instalando dependencias...
echo    Esto puede tomar varios minutos...
echo.

pip install --upgrade pip
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Fallo la instalacion de dependencias
    echo Revisa los errores arriba e intenta manualmente:
    echo   pip install -r requirements.txt
    pause
    exit /b 1
)

echo.
echo ================================================================================
echo  INSTALACION COMPLETADA
echo ================================================================================
echo.
echo Proximos pasos:
echo.
echo 1. Editar el archivo .env y configurar tu DOMINIO_API_RALF
echo 2. Asegurarte que ScraperRalf este corriendo en localhost:5000
echo 3. Verificar instalacion:
echo      python setup_check.py
echo.
echo 4. Iniciar el sistema:
echo      python app.py
echo.
echo ================================================================================
pause

#!/bin/bash
# =============================================================================
# Script de instalación automática para Linux/Mac
# =============================================================================

set -e

echo "================================================================================"
echo " INSTALACIÓN DEL SISTEMA MULTIAGENTE DE NOTICIAS"
echo "================================================================================"
echo ""

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 no está instalado"
    echo "Por favor instala Python 3.9 o superior"
    exit 1
fi

echo "[OK] Python detectado"
python3 --version
echo ""

# Verificar pip
if ! command -v pip3 &> /dev/null; then
    echo "[ERROR] pip3 no está instalado"
    exit 1
fi

# Preguntar por entorno virtual
echo "¿Deseas crear un entorno virtual? (Recomendado)"
read -p "Selecciona [S/n]: " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Ss]$ ]] || [[ -z $REPLY ]]; then
    echo "[*] Creando entorno virtual..."
    python3 -m venv venv
    
    echo "[*] Activando entorno virtual..."
    source venv/bin/activate
    
    echo "[OK] Entorno virtual activado"
fi

echo ""
echo "[*] Instalando dependencias..."
echo "   Esto puede tomar varios minutos..."
echo ""

pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "================================================================================"
echo " INSTALACIÓN COMPLETADA"
echo "================================================================================"
echo ""
echo "Próximos pasos:"
echo ""
echo "1. Editar el archivo .env y configurar tu DOMINIO_API_RALF"
echo "2. Asegurarte que ScraperRalf esté corriendo en localhost:5000"
echo "3. Verificar instalación:"
echo "     python setup_check.py"
echo ""
echo "4. Iniciar el sistema:"
echo "     python app.py"
echo ""
echo "================================================================================"

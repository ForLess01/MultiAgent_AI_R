"""
=============================================================================
SCRIPT DE VERIFICACIÓN Y CONFIGURACIÓN INICIAL
=============================================================================

Este script verifica que todos los requisitos estén satisfechos antes de
ejecutar el sistema multiagente.

Uso:
    python setup_check.py
"""

import os
import sys
from dotenv import load_dotenv

# Colores para terminal
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def print_header(text):
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}{text.center(80)}{RESET}")
    print(f"{BLUE}{'='*80}{RESET}\n")


def print_success(text):
    print(f"{GREEN}✓{RESET} {text}")


def print_error(text):
    print(f"{RED}✗{RESET} {text}")


def print_warning(text):
    print(f"{YELLOW}⚠{RESET} {text}")


def check_python_version():
    """Verifica versión de Python >= 3.9"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 9:
        print_success(f"Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print_error(f"Python {version.major}.{version.minor} (se requiere >= 3.9)")
        return False


def check_dependencies() -> tuple[bool, list[str]]:
    """Verifica que las dependencias estén instaladas"""
    required = ["flask", "flask_socketio", "crewai", "langchain", "dotenv", "requests"]

    missing: list[str] = []
    for package in required:
        try:
            __import__(package)
            print_success(f"Paquete '{package}' instalado")
        except ImportError:
            print_error(f"Paquete '{package}' NO instalado")
            missing.append(package)

    # Siempre retornar tupla (bool, list)
    return (len(missing) == 0, missing)


def check_env_file() -> tuple[bool, list[str]]:
    """Verifica que .env exista y tenga las variables necesarias"""
    if not os.path.exists(".env"):
        print_error("Archivo .env NO encontrado")
        return (False, [])

    load_dotenv()

    required_vars = ["DOMINIO_API_RALF", "RALF_MODEL_NAME", "SCRAPER_BASE_URL"]

    missing: list[str] = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Ocultar parte del valor por seguridad
            display = value[:20] + "..." if len(value) > 20 else value
            print_success(f"{var} = {display}")
        else:
            print_error(f"{var} NO configurado")
            missing.append(var)

    # Siempre retornar tupla (bool, list)
    return (len(missing) == 0, missing)


def check_directory_structure():
    """Verifica estructura de directorios"""
    required_dirs = ["src", "templates"]

    required_files = [
        "app.py",
        "src/llm_config.py",
        "src/tools.py",
        "src/callbacks.py",
        "src/crew.py",
        "templates/index.html",
    ]

    all_ok = True

    for directory in required_dirs:
        if os.path.exists(directory):
            print_success(f"Directorio '{directory}/' existe")
        else:
            print_error(f"Directorio '{directory}/' NO existe")
            all_ok = False

    for file in required_files:
        if os.path.exists(file):
            print_success(f"Archivo '{file}' existe")
        else:
            print_error(f"Archivo '{file}' NO existe")
            all_ok = False

    return all_ok


def test_api_connectivity():
    """Intenta conectar con las APIs"""
    import requests

    # Test ScraperRalf
    scraper_url = os.getenv("SCRAPER_BASE_URL", "http://localhost:5000")
    try:
        response = requests.get(
            f"{scraper_url}/api/search?q=test&max_results=1", timeout=5
        )
        if response.status_code == 200:
            print_success(f"ScraperRalf accesible en {scraper_url}")
        else:
            print_warning(
                f"ScraperRalf responde pero con código {response.status_code}"
            )
    except Exception as e:
        print_error(f"ScraperRalf NO accesible: {str(e)[:50]}")

    # Test API_RALF (más complejo, solo ping básico)
    ralf_domain = os.getenv("DOMINIO_API_RALF", "")
    if ralf_domain:
        try:
            # Intentar HEAD request a la base
            url = (
                f"https://{ralf_domain}"
                if not ralf_domain.startswith("http")
                else ralf_domain
            )
            response = requests.head(url, timeout=5, verify=False)
            print_success(f"API_RALF responde en {url}")
        except Exception as e:
            print_warning(
                f"API_RALF no responde (esto puede ser normal): {str(e)[:50]}"
            )


def main():
    print_header("VERIFICACIÓN DEL SISTEMA MULTIAGENTE")

    all_checks_passed = True

    # 1. Python
    print_header("1. Versión de Python")
    if not check_python_version():
        all_checks_passed = False

    # 2. Dependencias
    print_header("2. Dependencias de Python")
    deps_ok, missing_deps = check_dependencies()
    if not deps_ok:
        all_checks_passed = False
        print(f"\n{YELLOW}Instalar dependencias faltantes:{RESET}")
        print(f"  pip install {' '.join(missing_deps)}")

    # 3. Variables de entorno
    print_header("3. Variables de Entorno (.env)")
    env_ok, missing_vars = check_env_file()
    if not env_ok:
        all_checks_passed = False
        print(f"\n{YELLOW}Configurar en .env:{RESET}")
        if missing_vars:
            for var in missing_vars:
                print(f"  {var}=<tu-valor>")

    # 4. Estructura de archivos
    print_header("4. Estructura de Archivos")
    if not check_directory_structure():
        all_checks_passed = False

    # 5. Conectividad de APIs
    print_header("5. Conectividad de APIs")
    test_api_connectivity()

    # Resultado final
    print_header("RESULTADO FINAL")
    if all_checks_passed:
        print(
            f"{GREEN}✓ Todos los checks pasaron. Sistema listo para ejecutar.{RESET}\n"
        )
        print(f"{BLUE}Ejecutar:{RESET}")
        print(f"  python app.py\n")
        return 0
    else:
        print(f"{RED}✗ Algunos checks fallaron. Revisar errores arriba.{RESET}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())

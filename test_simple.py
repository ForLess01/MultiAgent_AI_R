"""
=============================================================================
SCRIPT DE PRUEBA SIMPLE - Genera artículo sin dashboard
=============================================================================

Este script permite probar el sistema multiagente directamente desde CLI,
sin necesidad de levantar el servidor Flask ni usar el dashboard web.

Uso:
    python test_simple.py "Tu tema de noticia"
"""

import sys
import os
from dotenv import load_dotenv

# Asegurar que el módulo src esté en el path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Cargar variables de entorno
load_dotenv()

from src.crew import generate_news_article


def main():
    """
    Función principal de prueba.
    """
    print("=" * 80)
    print(" SISTEMA MULTIAGENTE - MODO PRUEBA CLI")
    print("=" * 80)
    print()

    # Obtener tema
    if len(sys.argv) > 1:
        topic = " ".join(sys.argv[1:])
    else:
        topic = input("📰 Ingresa el tema de la noticia: ").strip()

    if not topic:
        print("❌ Error: Debes proporcionar un tema")
        sys.exit(1)

    print(f"\n🚀 Generando artículo sobre: '{topic}'")
    print("⏳ Este proceso puede tomar 1-3 minutos...\n")
    print("-" * 80)

    # Ejecutar crew
    try:
        result = generate_news_article(topic, session_id="cli-test")

        print("\n" + "=" * 80)

        if result["status"] == "success":
            print(" ✅ ARTÍCULO GENERADO EXITOSAMENTE")
            print("=" * 80)
            print()
            print(result["article"])
            print()
            print("=" * 80)
            print(f"✓ Sesión: {result['session_id']}")
            print("=" * 80)
            return 0
        else:
            print(" ❌ ERROR EN LA GENERACIÓN")
            print("=" * 80)
            print()
            print(f"Error: {result.get('error', 'Desconocido')}")
            print()
            print("=" * 80)
            return 1

    except KeyboardInterrupt:
        print("\n\n⚠️  Proceso interrumpido por el usuario")
        return 130

    except Exception as e:
        print("\n" + "=" * 80)
        print(" ❌ ERROR INESPERADO")
        print("=" * 80)
        print()
        print(f"Tipo: {type(e).__name__}")
        print(f"Mensaje: {str(e)}")
        print()
        print("=" * 80)
        print("\n🔧 Soluciones posibles:")
        print("  1. Verificar que API_RALF esté corriendo")
        print("  2. Verificar que ScraperRalf esté en localhost:5000")
        print("  3. Ejecutar: python setup_check.py")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())

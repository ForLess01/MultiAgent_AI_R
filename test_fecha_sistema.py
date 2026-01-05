"""
Script de prueba para verificar que el sistema maneja correctamente la fecha actual.

Este script prueba que todos los agentes reciben y usan la misma fecha de referencia,
solucionando el problema de "esquizofrenia temporal".

Ejecutar: python test_fecha_sistema.py
"""

import sys
import os

# Agregar src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from datetime import datetime

# Importación con manejo de errores
try:
    from src.crew import generate_news_article
except ImportError:
    try:
        # Intento alternativo sin src
        import crew  # type: ignore

        generate_news_article = crew.generate_news_article
    except ImportError:
        print(
            "Error: No se pudo importar crew. Asegúrate de estar en el directorio raíz del proyecto."
        )
        sys.exit(1)

print("=" * 100)
print("🧪 TEST DE SINCRONIZACIÓN TEMPORAL DEL SISTEMA")
print("=" * 100)
print()

# Fecha actual del sistema
current_date = datetime.now().strftime("%Y-%m-%d")
print(f"📅 Fecha actual del sistema: {current_date}")
print()

print("⚠️ NOTA: Este test requiere que estén corriendo:")
print("  1. ralf_proxy.py (puerto 11434)")
print("  2. ScraperRalf (puerto 5000)")
print()

input("Presiona ENTER para continuar o Ctrl+C para cancelar...")
print()

# Test 1: Verificar que la fecha se pasa correctamente
print("=" * 100)
print("TEST 1: Verificar paso de fecha a través del sistema")
print("=" * 100)
print()

print(f"🔵 Llamando a generate_news_article con fecha explícita: {current_date}")
print()

try:
    # Ejecutar generación con fecha explícita
    result = generate_news_article(
        topic="Prueba de sincronización temporal",
        session_id="test-fecha",
        current_date=current_date,
    )

    print("✅ Sistema ejecutado correctamente")
    print(f"Status: {result.get('status')}")

    if result.get("status") == "success":
        article = result.get("article", "")
        print(f"\n📰 Artículo generado ({len(article)} caracteres)")
        print("\nPrimeros 500 caracteres:")
        print("-" * 100)
        print(article[:500])
        print("-" * 100)
    else:
        print(f"\n⚠️ Error: {result.get('error', 'Desconocido')}")
        print(f"\n📋 Detalles:")
        print(result)

except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback

    traceback.print_exc()

print()
print("=" * 100)
print("TEST 2: Verificar logs del Analista")
print("=" * 100)
print()
print("Revisa los logs arriba y confirma que:")
print(
    "  ✅ El Investigador vio el mensaje: 'CONTEXTO TEMPORAL IMPORTANTE: HOY ES {current_date}'"
)
print("  ✅ El Analista vio el mensaje: 'ANALISTA - FECHA DE CONTEXTO: {current_date}'")
print("  ✅ El Analista NO rechazó noticias por 'anomalías temporales'")
print()
print("=" * 100)
print()

print("🎯 VERIFICACIÓN FINAL")
print()
print("Si el sistema funcionó correctamente, deberías haber visto:")
print()
print(f"  1. 📅 'Fecha de referencia del sistema: {current_date}'")
print(f"  2. 🔴 'INVESTIGADOR LLAMÓ A LA HERRAMIENTA NewsSearchTool'")
print(f"  3. 🟢 'HERRAMIENTA COMPLETADA - DATOS RECIBIDOS'")
print(f"  4. 🔍 'ANALISTA - FECHA DE CONTEXTO: {current_date}'")
print(f"  5. ✅ 'FASE 3: Redacción' (si el Analista APROBÓ)")
print()
print("Si el Analista RECHAZÓ por 'anomalías temporales', el problema persiste.")
print("Si el Analista APROBÓ, la esquizofrenia temporal está SOLUCIONADA ✅")
print()
print("=" * 100)

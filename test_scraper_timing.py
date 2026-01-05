"""
Script de verificación de tiempos de ScraperRalf.

Este script prueba que el sistema espera correctamente a que todas las fuentes
de ScraperRalf completen su búsqueda antes de procesar los resultados.

Ejecutar: python test_scraper_timing.py
"""

import time
import requests
import json
from datetime import datetime

# Configuración
SCRAPER_URL = "http://127.0.0.1:5000/api/search"
TEST_QUERY = "inteligencia artificial"

print("=" * 80)
print("🧪 TEST DE INTEGRACIÓN CON SCRAPERRALF")
print("=" * 80)
print()

# Verificar que ScraperRalf esté corriendo
print("1️⃣ Verificando que ScraperRalf esté disponible...")
try:
    health_check = requests.get("http://127.0.0.1:5000/", timeout=5)
    if health_check.status_code == 200:
        print("   ✅ ScraperRalf está corriendo en http://127.0.0.1:5000")
    else:
        print(f"   ⚠️ ScraperRalf responde con código {health_check.status_code}")
except Exception as e:
    print(f"   ❌ ERROR: ScraperRalf NO está disponible: {e}")
    print("   💡 Solución: Ejecuta 'python app.py' en el directorio de ScraperRalf")
    exit(1)

print()
print("2️⃣ Ejecutando búsqueda con timeout de 90 segundos...")
print(f"   Query: '{TEST_QUERY}'")
print(f"   Max results: 5 por fuente")
print()

# Medir tiempo de ejecución
start_time = time.time()
start_datetime = datetime.now()

print(f"   ⏱️ Inicio: {start_datetime.strftime('%H:%M:%S')}")
print("   ⏳ Esperando respuesta (esto puede tardar hasta 90 segundos)...")
print()

try:
    response = requests.get(
        SCRAPER_URL,
        params={"q": TEST_QUERY, "max_results": 5},
        timeout=90,  # Mismo timeout que en tools.py
        headers={"User-Agent": "MultiAgent-NewsSystem-Test/1.0"},
    )

    end_time = time.time()
    elapsed_time = end_time - start_time

    print(f"   ✅ Respuesta recibida en {elapsed_time:.2f} segundos")
    print()

    # Parsear respuesta
    data = response.json()

    # Análisis de resultados
    print("3️⃣ Análisis de Resultados:")
    print("   " + "-" * 76)

    if "results" in data:
        results = data["results"]
        total_results = len(results)

        print(f"   Total de artículos: {total_results}")
        print()

        # Clasificar por fuente
        sources = {}
        for result in results:
            source = result.get("source", "Desconocido")
            if source not in sources:
                sources[source] = []
            sources[source].append(result)

        print("   📊 Distribución por fuente:")
        print()

        # Tier 1: Fuentes locales
        tier1_sources = ["La República", "El Comercio", "Infobae"]
        tier1_count = 0
        tier1_total_chars = 0

        print("   🟢 TIER 1 - Fuentes Locales (Contenido Completo):")
        for source_name in tier1_sources:
            if source_name in sources:
                articles = sources[source_name]
                tier1_count += len(articles)

                for article in articles:
                    content_length = len(article.get("content", ""))
                    tier1_total_chars += content_length

                print(f"      • {source_name}: {len(articles)} artículo(s)")
                print(
                    f"        Longitud promedio: {content_length / len(articles):.0f} caracteres"
                )
                print(f"        Método: {article.get('method', 'N/A')}")

        print()

        # Tier 2: APIs globales
        tier2_sources = ["NewsAPI", "TheNewsAPI"]
        tier2_count = 0
        tier2_total_chars = 0

        print("   🟡 TIER 2 - APIs Globales (Snippets):")
        for source_name in tier2_sources:
            if source_name in sources:
                articles = sources[source_name]
                tier2_count += len(articles)

                for article in articles:
                    content_length = len(article.get("content", ""))
                    tier2_total_chars += content_length

                print(f"      • {source_name}: {len(articles)} artículo(s)")
                if len(articles) > 0:
                    print(
                        f"        Longitud promedio: {content_length / len(articles):.0f} caracteres"
                    )

        print()
        print("   " + "-" * 76)
        print()

        # Resumen
        print("4️⃣ Resumen de Calidad:")
        print()
        print(f"   ✅ Fuentes Tier 1 (profundas): {tier1_count} artículos")
        if tier1_count > 0:
            print(
                f"      → Promedio de longitud: {tier1_total_chars / tier1_count:.0f} caracteres"
            )
            print(f"      → Total de contenido: {tier1_total_chars:,} caracteres")

        print()
        print(f"   ✅ Fuentes Tier 2 (APIs): {tier2_count} artículos")
        if tier2_count > 0:
            print(
                f"      → Promedio de longitud: {tier2_total_chars / tier2_count:.0f} caracteres"
            )

        print()
        print("   " + "-" * 76)
        print()

        # Verificación de timeout
        print("5️⃣ Verificación de Timeout:")
        print()

        if elapsed_time < 10:
            print("   ⚠️ ADVERTENCIA: La búsqueda fue muy rápida (<10s)")
            print("      Esto sugiere que solo se consultaron las APIs globales.")
            print("      Las fuentes locales probablemente fallaron o no se esperaron.")
        elif elapsed_time < 45:
            print("   ⚠️ ADVERTENCIA: La búsqueda fue rápida (<45s)")
            print("      Es posible que Infobae haya hecho timeout.")
            print("      Verifica que Camoufox esté instalado: 'camoufox fetch'")
        elif elapsed_time >= 45 and tier1_count >= 6:
            print("   ✅ PERFECTO: La búsqueda tomó suficiente tiempo y obtuvo")
            print("      artículos completos de fuentes locales.")
            print(f"      Tiempo: {elapsed_time:.1f}s es apropiado para obtener")
            print("      contenido de El Comercio, La República e Infobae.")
        else:
            print(f"   ℹ️ INFO: Búsqueda completada en {elapsed_time:.1f}s")
            print(f"      Se obtuvieron {tier1_count} artículos de fuentes locales.")

        print()

        # Verificación de contenido completo
        print("6️⃣ Verificación de Contenido Completo:")
        print()

        has_full_content = False
        for result in results:
            content = result.get("content", "")
            if len(content) > 1000 and result.get("source") in tier1_sources:
                has_full_content = True
                print(f"   ✅ Artículo completo detectado:")
                print(f"      Fuente: {result.get('source')}")
                print(f"      Título: {result.get('title', 'N/A')[:60]}...")
                print(f"      Longitud: {len(content):,} caracteres")
                print(f"      Primeros 150 caracteres:")
                print(f'      "{content[:150]}..."')
                print()
                break

        if not has_full_content:
            print("   ❌ NO se detectaron artículos completos (>1000 chars)")
            print("      Esto indica que las fuentes locales no completaron.")

        print()

    else:
        print("   ❌ ERROR: Respuesta sin campo 'results'")
        print(f"   Respuesta: {json.dumps(data, indent=2)}")

    print("=" * 80)
    print()

    # Conclusión
    if tier1_count >= 3 and has_full_content:
        print("🎉 CONCLUSIÓN: El sistema está funcionando CORRECTAMENTE")
        print("   • El timeout de 90s es respetado")
        print("   • Las fuentes locales están entregando contenido completo")
        print("   • El Investigator recibirá información de calidad")
    elif tier1_count > 0 and has_full_content:
        print("⚠️ CONCLUSIÓN: El sistema funciona PARCIALMENTE")
        print("   • Algunas fuentes locales están funcionando")
        print(f"   • Solo {tier1_count} de 9 posibles fuentes locales respondieron")
        print("   • Verifica que todas las APIs locales estén configuradas")
    else:
        print("❌ CONCLUSIÓN: El sistema NO está obteniendo contenido completo")
        print("   • Las fuentes locales no están respondiendo")
        print("   • Posibles causas:")
        print("     1. ScraperRalf no tiene configuradas las fuentes locales")
        print("     2. Infobae requiere 'camoufox fetch'")
        print("     3. Timeout demasiado bajo en ScraperRalf")
        print("     4. Problemas de red/firewall")

    print()
    print("=" * 80)

except requests.Timeout:
    end_time = time.time()
    elapsed_time = end_time - start_time
    print()
    print(f"   ❌ TIMEOUT después de {elapsed_time:.2f} segundos")
    print()
    print("   🔍 Diagnóstico:")
    print("      El timeout de 90s fue excedido. Esto puede indicar:")
    print("      1. ScraperRalf está tardando más de 90s (muy poco probable)")
    print("      2. ScraperRalf se colgó y no respondió")
    print("      3. Problema de red/firewall")
    print()
    print("   💡 Soluciones:")
    print("      1. Revisa los logs de ScraperRalf: tail -f project.log")
    print("      2. Verifica que Infobae/Camoufox esté funcionando")
    print("      3. Intenta con una query más simple: 'economía'")

except Exception as e:
    print()
    print(f"   ❌ ERROR: {type(e).__name__}: {e}")
    print()
    print("   💡 Verifica que ScraperRalf esté corriendo correctamente")

print()

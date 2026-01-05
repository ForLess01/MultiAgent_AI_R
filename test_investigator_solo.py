"""
Test de Diagnóstico: ¿El Investigador espera a ScraperRalf?
===========================================================

Este script prueba SOLO el agente Investigador para verificar si:
1. Llama a la herramienta news_search
2. Espera los 60-70 segundos completos
3. Procesa los datos recibidos correctamente

Ejecutar con:
    python test_investigator_solo.py
"""

import sys
import os
import time
from datetime import datetime

# Agregar path para imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.crew import create_investigator_agent, create_investigation_task
from crewai import Crew, Process


def main():
    print("=" * 100)
    print("🧪 TEST DE DIAGNÓSTICO: TIMEOUT DEL INVESTIGADOR")
    print("=" * 100)
    print()
    print("Objetivo: Verificar si el Investigador espera los 60-70s necesarios")
    print("Configuración esperada:")
    print("  - LLM timeout: 120s")
    print("  - Tool timeout: 90s")
    print("  - ScraperRalf tiempo real: ~67s")
    print()
    print("=" * 100)
    input("Presiona ENTER para iniciar el test...")
    print()

    # Crear agente y tarea
    print("📋 Creando Investigador...")
    investigator = create_investigator_agent()

    print("📋 Creando tarea de investigación...")
    task = create_investigation_task(
        investigator,
        "Captura de Nicolás Maduro en Venezuela",  # Tema real que tiene datos
        "2026-01-04",
    )

    # Crew minimalista
    print("📋 Creando Crew...")
    crew = Crew(
        agents=[investigator],
        tasks=[task],
        process=Process.sequential,
        verbose=True,  # Logs detallados
    )

    # Cronometrar
    print()
    print("=" * 100)
    print("⏱️  INICIANDO EJECUCIÓN")
    print("=" * 100)
    start_wall_time = time.time()
    start_human_time = datetime.now().strftime("%H:%M:%S")
    print(f"🕐 Hora de inicio: {start_human_time}")
    print()
    print("⚠️  IMPORTANTE: Observa los logs para ver:")
    print("   1. 🔴 Mensaje 'INVESTIGADOR LLAMÓ A LA HERRAMIENTA'")
    print("   2. ⏳ Espera silenciosa de ~60-70 segundos")
    print("   3. 🟢 Mensaje 'HERRAMIENTA COMPLETADA'")
    print()
    print("-" * 100)

    # Ejecutar
    try:
        result = crew.kickoff()
    except Exception as e:
        print()
        print("=" * 100)
        print("❌ ERROR DURANTE LA EJECUCIÓN")
        print("=" * 100)
        print(f"Tipo: {type(e).__name__}")
        print(f"Mensaje: {str(e)}")
        print("=" * 100)
        return

    # Resultados
    end_wall_time = time.time()
    end_human_time = datetime.now().strftime("%H:%M:%S")
    elapsed = end_wall_time - start_wall_time

    print()
    print("=" * 100)
    print("⏱️  EJECUCIÓN COMPLETADA")
    print("=" * 100)
    print(f"🕐 Hora de inicio: {start_human_time}")
    print(f"🕐 Hora de fin:    {end_human_time}")
    print(f"⏱️  Tiempo total:   {elapsed:.2f} segundos")
    print("=" * 100)
    print()

    # Análisis automático
    print("=" * 100)
    print("📊 ANÁLISIS AUTOMÁTICO")
    print("=" * 100)

    result_str = str(result).lower()

    # Verificar tiempo
    if elapsed < 30:
        print("❌ PROBLEMA CRÍTICO: Terminó en menos de 30 segundos")
        print("   → El Investigador NO llamó a la herramienta O no esperó")
        print("   → Posible causa: Agente decidió 'finalizar' prematuramente")
        verdict = "FALLO"
    elif elapsed < 60:
        print("⚠️  SOSPECHOSO: Terminó entre 30-60 segundos")
        print("   → Puede que solo usó APIs rápidas (NewsAPI, TheNewsAPI)")
        print("   → No esperó a scrapers locales (La República, El Comercio, Infobae)")
        verdict = "DUDOSO"
    elif elapsed >= 60:
        print("✅ TIEMPO CORRECTO: Tardó >= 60 segundos")
        print("   → Probablemente esperó a ScraperRalf completamente")
        verdict = "ÉXITO"
    else:
        verdict = "DESCONOCIDO"

    print()

    # Verificar menciones clave en el output
    checks = {
        "Menciona 'Tier 1' o 'deep'": any(
            x in result_str for x in ["tier 1", "tier 2", "deep", "profund"]
        ),
        "Incluye URLs de fuentes": "http" in result_str
        or "larepublica" in result_str
        or "elcomercio" in result_str,
        "Confirma tiempo de espera": any(
            x in result_str for x in ["esperé", "segundos", "recibí respuesta"]
        ),
        "Contiene citas textuales": '"' in str(result) and ">" in str(result),
        "Menciona 'deep_sources_count'": "deep_sources_count" in result_str
        or "artículos tier" in result_str,
    }

    print("Verificaciones de contenido:")
    all_passed = True
    for check, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"  {status} {check}")
        if not passed:
            all_passed = False

    print()
    print("=" * 100)
    print("🎯 VEREDICTO FINAL")
    print("=" * 100)

    if verdict == "ÉXITO" and all_passed:
        print("✅ ✅ ✅ TODO CORRECTO ✅ ✅ ✅")
        print("El Investigador:")
        print("  1. Llamó a la herramienta correctamente")
        print("  2. Esperó los ~60-70 segundos necesarios")
        print("  3. Procesó los datos de ScraperRalf")
        print("  4. Generó un informe completo con fuentes Tier 1")
    elif verdict == "ÉXITO":
        print("⚠️  PARCIALMENTE CORRECTO")
        print("El tiempo fue adecuado PERO el contenido es sospechoso")
        print(
            "  → Posible problema: Agente inventó datos o no procesó bien la respuesta"
        )
    else:
        print("❌ ❌ ❌ PROBLEMA DETECTADO ❌ ❌ ❌")
        print(f"Resultado: {verdict}")
        print()
        print("🔧 ACCIONES SUGERIDAS:")
        if elapsed < 30:
            print("  1. Verificar que ralf_proxy.py está corriendo")
            print("  2. Revisar logs para ver si aparece '🔴 INVESTIGADOR LLAMÓ'")
            print("  3. Si no aparece, el agente no está usando la herramienta")
            print("     → Solución: Forzar tool_choice='required' en llm_config.py")
        elif elapsed < 60:
            print(
                "  1. El agente puede estar terminando antes de recibir datos completos"
            )
            print("  2. Revisar si hay mensajes de timeout en logs")
            print("  3. Considerar aumentar max_iter o agregar early_stopping=False")

    print("=" * 100)
    print()

    # Mostrar extracto del resultado
    print("=" * 100)
    print("📄 EXTRACTO DEL RESULTADO (primeros 1000 caracteres)")
    print("=" * 100)
    print(str(result)[:1000])
    if len(str(result)) > 1000:
        print(f"\n... ({len(str(result)) - 1000} caracteres más)\n")
    print("=" * 100)

    # Preguntar si quiere ver el resultado completo
    print()
    respuesta = input("¿Deseas ver el resultado completo? (s/n): ")
    if respuesta.lower() in ["s", "si", "sí", "y", "yes"]:
        print()
        print("=" * 100)
        print("📄 RESULTADO COMPLETO")
        print("=" * 100)
        print(str(result))
        print("=" * 100)


if __name__ == "__main__":
    main()

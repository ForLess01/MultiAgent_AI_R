"""
=============================================================================
MÓDULO: Herramientas Personalizadas (Los "Ojos" del Sistema)
=============================================================================

Implementa herramientas personalizadas que conectan con APIs locales
para recopilación de información, evitando dependencias de servicios externos.

FUNDAMENTACIÓN TEÓRICA:
- Sensores del Agente (Russell & Norvig, Cap. 2.3)
- Los agentes perciben el entorno mediante herramientas especializadas
- ScraperRalf actúa como interfaz sensorial con el mundo de noticias

ARQUITECTURA:
- Herramientas basadas en BaseTool de CrewAI/LangChain
- Conexión HTTP con API local de scraping
- Manejo robusto de errores y timeouts
"""

import os
import requests
from typing import Type, Optional, List, Dict, Any, TYPE_CHECKING
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import logging
import json

# Importar BaseTool - priorizar crewai.tools
try:
    from crewai.tools import BaseTool  # type: ignore[import]
except ImportError:
    from crewai_tools import BaseTool  # type: ignore[import]

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()


class NewsSearchInput(BaseModel):
    """
    Esquema de entrada para la herramienta de búsqueda de noticias.

    Teoría (AIMA Cap. 2.3):
    - Define la "percepción" que el agente solicita del entorno
    - query: pregunta en lenguaje natural
    - max_results: límite de recursos computacionales
    """

    query: str = Field(
        ...,
        description="Consulta de búsqueda en lenguaje natural. "
        "Ejemplo: 'inteligencia artificial en medicina'",
    )
    max_results: int = Field(
        default=5, description="Número máximo de resultados a retornar (1-20)"
    )


class NewsSearchTool(BaseTool):  # type: ignore[misc]
    """
    Herramienta de búsqueda de noticias mediante ScraperRalf API.

    TEORÍA APLICADA (AIMA Cap. 16):
    - Implementa un "Agente de Recopilación de Información"
    - Abstrae la complejidad de múltiples fuentes web
    - Retorna datos estructurados listos para razonamiento

    DISEÑO:
    - Tolerante a fallos (manejo de timeouts y errores HTTP)
    - Validación de entrada mediante Pydantic
    - Logging detallado para debugging
    """

    name: str = "news_search"
    description: str = (
        "Busca noticias y artículos en fuentes confiables mediante la API ScraperRalf. "
        "Usa esta herramienta cuando necesites información actualizada sobre un tema específico. "
        "Retorna título, contenido y fuente de cada artículo encontrado. "
        "IMPORTANTE: Siempre verifica la calidad de las fuentes antes de usar la información."
    )
    args_schema: Type[BaseModel] = NewsSearchInput

    # Campos de configuración (Pydantic fields)
    base_url: str = Field(
        default_factory=lambda: os.getenv("SCRAPER_BASE_URL", "http://127.0.0.1:5000")
    )
    default_max_results: int = Field(
        default_factory=lambda: int(os.getenv("SCRAPER_MAX_RESULTS", "5"))
    )

    def _run(self, query: str, max_results: Optional[int] = None) -> str:
        """
        Ejecuta la búsqueda de noticias.

        Args:
            query: Consulta de búsqueda
            max_results: Límite de resultados (usa default si no se especifica)

        Returns:
            String JSON con resultados estructurados o mensaje de error

        Teoría (AIMA Cap. 2.4):
        - Mapeo de acción (búsqueda) a percepción (resultados)
        - Manejo de incertidumbre (errores de red, datos faltantes)
        """
        if max_results is None:
            max_results = self.default_max_results

        # Validar rango de max_results
        max_results = max(1, min(max_results, 20))

        import time
        from datetime import datetime

        start_time = time.time()
        start_datetime = datetime.now().strftime("%H:%M:%S")

        # LOGGING EXTREMADAMENTE VISIBLE
        print("\n" + "=" * 100)
        print("🔴🔴🔴 INVESTIGADOR LLAMÓ A LA HERRAMIENTA NewsSearchTool 🔴🔴🔴")
        print("=" * 100)
        logger.info(f"\n{'='*80}")
        logger.info(f"🔎 INICIO BÚSQUEDA: '{query}' (max: {max_results} por fuente)")
        logger.info(f"⏱️ Timestamp: {start_datetime}")
        logger.info(
            f"⚠️ ESTA OPERACIÓN TARDARÁ ~60-70 SEGUNDOS - EL INVESTIGADOR DEBE ESPERAR"
        )
        logger.info(f"{'='*80}\n")

        print(
            f"⏳ ESPERANDO RESPUESTA DE SCRAPERRALF... (esto puede tardar 60-70 segundos)"
        )
        print(f"🚫 EL INVESTIGADOR NO DEBE CONTINUAR HASTA QUE ESTO COMPLETE")
        print("=" * 100 + "\n")

        try:
            # Construcción de la petición
            endpoint = f"{self.base_url}/api/search"
            params = {"q": query, "max_results": max_results}

            # Timeout de 90s para permitir que scrapers locales completen
            # (Infobae con browser automation puede tardar 60-90s)
            # ScraperRalf ejecuta las 5 fuentes en paralelo:
            # - APIs globales (NewsAPI, TheNewsAPI): ~3-5s
            # - El Comercio (JSON-LD): ~30-45s
            # - La República (CSS): ~45-60s
            # - Infobae (Camoufox): ~60-90s
            response = requests.get(
                endpoint,
                params=params,
                timeout=90,  # Timeout aumentado para contenido completo
                headers={"User-Agent": "MultiAgent-NewsSystem/1.0"},
            )

            # Verificar código de estado
            response.raise_for_status()

            # Parsear respuesta
            data = response.json()

            elapsed_time = time.time() - start_time
            end_datetime = datetime.now().strftime("%H:%M:%S")

            # LOGGING EXTREMADAMENTE VISIBLE
            print("\n" + "=" * 100)
            print(
                "🟢🟢🟢 HERRAMIENTA COMPLETADA - DATOS RECIBIDOS DE SCRAPERRALF 🟢🟢🟢"
            )
            print("=" * 100)
            logger.info(f"\n{'='*80}")
            logger.info(f"✅ RESPUESTA RECIBIDA en {elapsed_time:.2f} segundos")
            logger.info(f"⏱️ Inicio: {start_datetime} → Fin: {end_datetime}")
            logger.info(f"{'='*80}\n")
            print(f"⏱️ Tiempo de espera: {elapsed_time:.2f} segundos")
            print(f"✅ EL INVESTIGADOR AHORA TIENE LOS DATOS COMPLETOS")
            print("=" * 100 + "\n")

            # Validar estructura de respuesta
            if "results" not in data:
                logger.warning("⚠️ Respuesta sin campo 'results'")
                return json.dumps(
                    {
                        "status": "error",
                        "message": "Formato de respuesta inválido de ScraperRalf",
                        "results": [],
                    }
                )

            results = data["results"]
            logger.info(f"📦 Total de artículos recibidos: {len(results)}")

            # Contar artículos por tier
            deep_sources = sum(
                1
                for r in results
                if r.get("source") in ["La República", "El Comercio", "Infobae"]
            )
            api_sources = sum(
                1 for r in results if r.get("source") in ["NewsAPI", "TheNewsAPI"]
            )

            logger.info(f"\n📊 ANÁLISIS DE DISTRIBUCIÓN POR TIER:")
            logger.info(
                f"   🟢 TIER 1 (Fuentes Locales/Deep): {deep_sources} artículos"
            )
            logger.info(f"   🟡 TIER 2 (APIs Globales): {api_sources} artículos")

            # Análisis de longitud de contenido
            if deep_sources > 0:
                deep_articles = [
                    r
                    for r in results
                    if r.get("source") in ["La República", "El Comercio", "Infobae"]
                ]
                avg_length = sum(
                    len(r.get("content", "")) for r in deep_articles
                ) / len(deep_articles)
                total_chars = sum(len(r.get("content", "")) for r in deep_articles)
                logger.info(
                    f"   📏 Longitud promedio Tier 1: {avg_length:.0f} caracteres"
                )
                logger.info(
                    f"   📝 Total de contenido Tier 1: {total_chars:,} caracteres"
                )

            if api_sources > 0:
                api_articles = [
                    r for r in results if r.get("source") in ["NewsAPI", "TheNewsAPI"]
                ]
                avg_length_api = sum(
                    len(r.get("content", "")) for r in api_articles
                ) / len(api_articles)
                logger.info(
                    f"   📏 Longitud promedio Tier 2: {avg_length_api:.0f} caracteres"
                )

            logger.info(f"")

            # Formatear resultados para consumo del agente
            formatted_results = []
            for idx, item in enumerate(results, 1):
                # Clasificar fuentes por tier (calidad de contenido)
                source = item.get("source", "Fuente desconocida")
                content = item.get("content", "Sin contenido")

                # Tier 1: Fuentes locales con contenido completo
                is_deep_source = source in ["La República", "El Comercio", "Infobae"]

                # Tier 2: APIs globales con snippets
                is_api_source = source in ["NewsAPI", "TheNewsAPI"]

                formatted_results.append(
                    {
                        "id": idx,
                        "title": item.get("title", "Sin título"),
                        "content": content,
                        "source": source,
                        "url": item.get("url", ""),
                        "date": item.get("date", ""),
                        "tier": (
                            "deep"
                            if is_deep_source
                            else ("api" if is_api_source else "unknown")
                        ),
                        "content_length": len(content),
                        "extraction_method": item.get("method", "unknown"),
                    }
                )

            return json.dumps(
                {
                    "status": "success",
                    "query": query,
                    "total_results": len(formatted_results),
                    "deep_sources_count": sum(
                        1 for r in formatted_results if r["tier"] == "deep"
                    ),
                    "api_sources_count": sum(
                        1 for r in formatted_results if r["tier"] == "api"
                    ),
                    "results": formatted_results,
                },
                indent=2,
                ensure_ascii=False,
            )

        except requests.Timeout:
            error_msg = f"⏱️ Timeout al conectar con ScraperRalf ({self.base_url})"
            logger.error(error_msg)
            return json.dumps(
                {
                    "status": "error",
                    "message": "La búsqueda excedió el tiempo límite. Intenta con una consulta más específica.",
                    "results": [],
                }
            )

        except requests.ConnectionError:
            error_msg = f"🔌 No se pudo conectar con ScraperRalf en {self.base_url}"
            logger.error(error_msg)
            return json.dumps(
                {
                    "status": "error",
                    "message": f"ScraperRalf no está disponible. Verifica que el servicio esté corriendo en {self.base_url}",
                    "results": [],
                }
            )

        except requests.HTTPError as e:
            error_msg = f"❌ Error HTTP {e.response.status_code}: {e.response.text}"
            logger.error(error_msg)
            return json.dumps(
                {
                    "status": "error",
                    "message": f"Error del servidor de búsqueda: {e.response.status_code}",
                    "results": [],
                }
            )

        except Exception as e:
            error_msg = f"💥 Error inesperado en NewsSearchTool: {str(e)}"
            logger.error(error_msg)
            return json.dumps(
                {
                    "status": "error",
                    "message": f"Error interno: {type(e).__name__}",
                    "results": [],
                }
            )


class FactCheckInput(BaseModel):
    """
    Esquema para verificación de hechos (herramienta futura).
    """

    statement: str = Field(..., description="Afirmación a verificar")


class FactCheckTool(BaseTool):  # type: ignore[misc]
    """
    Herramienta de verificación de hechos (placeholder para expansión futura).

    TEORÍA (AIMA Cap. 12.5):
    - Monitoreo de Ejecución requiere validación de precondiciones
    - Esta herramienta permitiría al Analista verificar claims automáticamente

    NOTA: Requiere implementar endpoint en ScraperRalf o servicio externo
    """

    name: str = "fact_check"
    description: str = (
        "Verifica la veracidad de afirmaciones contrastándolas con fuentes confiables. "
        "Usa esta herramienta cuando necesites validar un dato específico. "
        "Retorna: verificado, no verificado, o información insuficiente."
    )
    args_schema: Type[BaseModel] = FactCheckInput

    def _run(self, statement: str) -> str:
        """
        Placeholder: En producción, conectaría con fact-checking API.
        """
        logger.warning("⚠️ FactCheckTool aún no implementada. Retornando placeholder.")
        return json.dumps(
            {
                "status": "not_implemented",
                "message": "Sistema de fact-checking en desarrollo. Usa análisis manual por ahora.",
                "statement": statement,
                "verdict": "requires_manual_review",
            }
        )


# Factory function para instanciar herramientas
def get_news_search_tool() -> NewsSearchTool:
    """
    Retorna una instancia configurada de NewsSearchTool.

    Returns:
        Herramienta lista para usar en agentes
    """
    return NewsSearchTool()


def get_fact_check_tool() -> FactCheckTool:
    """
    Retorna una instancia de FactCheckTool (placeholder).
    """
    return FactCheckTool()


if __name__ == "__main__":
    """
    Test de integración con ScraperRalf.
    """
    print("🧪 Probando NewsSearchTool...\n")

    tool = get_news_search_tool()

    # Test de búsqueda
    result = tool._run("inteligencia artificial", max_results=3)
    print("📰 Resultado de búsqueda:")
    print(result)
    print("\n" + "=" * 80 + "\n")

    # Parsear resultado para verificar
    try:
        data = json.loads(result)
        if data["status"] == "success":
            print(f"✅ Test exitoso: {data['total_results']} artículos encontrados")
        else:
            print(f"⚠️ Test completado con advertencias: {data['message']}")
    except Exception as e:
        print(f"❌ Error parseando resultado: {e}")

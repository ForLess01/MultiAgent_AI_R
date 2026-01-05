"""
=============================================================================
MÓDULO: Configuración del LLM Personalizado (API_RALF)
=============================================================================

Implementa la integración con un LLM desplegado en infraestructura propia,
usando un proxy local que convierte el formato OpenAI al formato de API_RALF.

FUNDAMENTACIÓN TEÓRICA:
- Basado en Agentes Basados en Utilidad (Russell & Norvig, Cap. 2.4)
- El LLM actúa como "función de mapeo" de percepciones a acciones
- Permite razonamiento deliberativo para planificación HTN (Cap. 11.3)

ARQUITECTURA:
- Usa ChatOpenAI de LangChain apuntando a proxy local
- Proxy traduce formato OpenAI → formato API_RALF
- Endpoint: http://127.0.0.1:11434/v1 (proxy) → API_RALF real
"""

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from typing import Optional
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()


class CustomLLMConfig:
    """
    Configurador del LLM personalizado para el sistema multiagente.

    Teoría Aplicada (AIMA Cap. 2):
    - Abstracción del "Agente Racional" donde el LLM es el motor de decisión
    - Permite inyección de dependencias para testing y modularidad
    """

    def __init__(self):
        """
        Inicializa la configuración leyendo variables de entorno.
        """
        self.base_url = os.getenv("RALF_PROXY_URL", "http://127.0.0.1:11434/v1")
        self.api_key = os.getenv("OPENAI_API_KEY", "sk-proxy-not-used")
        self.model_name = os.getenv("RALF_MODEL_NAME", "ralf-mixed-model")
        self.temperature = 0.7

        logger.info(f"🧠 LLM Configurado: {self.base_url} | Modelo: {self.model_name}")

    def get_llm(
        self, temperature: Optional[float] = None, max_tokens: int = 2000
    ) -> ChatOpenAI:
        """
        Retorna una instancia configurada de ChatOpenAI usando el proxy.

        Args:
            temperature: Control de aleatoriedad (0.0-1.0)
            max_tokens: Límite de tokens en respuesta

        Returns:
            Instancia de ChatOpenAI lista para usar en agentes
        """
        temp = temperature if temperature is not None else self.temperature

        try:
            logger.info(
                f"🔧 Creando LLM con base_url={self.base_url}, model={self.model_name}"
            )

            # IMPORTANTE: Configurar también como variable de entorno
            os.environ["OPENAI_API_BASE"] = self.base_url
            os.environ["OPENAI_BASE_URL"] = self.base_url

            llm = ChatOpenAI(
                openai_api_base=self.base_url,  # Parámetro legacy
                base_url=self.base_url,  # Parámetro moderno
                api_key=self.api_key,  # type: ignore
                model=self.model_name,
                temperature=temp,
                max_tokens=max_tokens,
                timeout=120,  # Aumentado de 60 a 120s para herramientas lentas (ScraperRalf ~67s)
                max_retries=3,
                model_kwargs={
                    # Forzar uso de herramientas cuando estén disponibles
                    # Esto previene que el LLM invente datos en lugar de usar tools
                    "tool_choice": "auto",  # auto permite que use tools cuando sea apropiado
                },
            )

            # Verificar configuración
            logger.info(f"🔍 OPENAI_API_BASE={os.getenv('OPENAI_API_BASE')}")

            logger.info(f"✅ LLM instanciado correctamente (temp={temp})")
            return llm

        except Exception as e:
            logger.error(f"❌ Error al crear instancia LLM: {e}")
            raise


# Singleton para reutilización
_llm_config_instance = None


def get_llm_config() -> CustomLLMConfig:
    """
    Patrón Singleton para evitar múltiples cargas de configuración.
    """
    global _llm_config_instance
    if _llm_config_instance is None:
        _llm_config_instance = CustomLLMConfig()
    return _llm_config_instance


# Factory functions para distintos perfiles de agente
def get_investigator_llm() -> ChatOpenAI:
    """LLM optimizado para el Investigador (baja temperature, alta precisión)."""
    config = get_llm_config()
    return config.get_llm(temperature=0.3)


def get_analyst_llm() -> ChatOpenAI:
    """LLM optimizado para el Analista de Sesgos (temperature media)."""
    config = get_llm_config()
    return config.get_llm(temperature=0.5)


def get_writer_llm() -> ChatOpenAI:
    """LLM optimizado para el Redactor (alta temperature, creatividad)."""
    config = get_llm_config()
    return config.get_llm(temperature=0.8, max_tokens=3000)


def get_manager_llm() -> ChatOpenAI:
    """LLM para el Jefe de Redacción (temperature balanceada)."""
    config = get_llm_config()
    return config.get_llm(temperature=0.6)

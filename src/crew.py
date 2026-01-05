"""
=============================================================================
MÓDULO: Sistema Multiagente de Producción de Noticias
=============================================================================

Implementa una Crew de Agentes Inteligentes basada en Planificación HTN
(Hierarchical Task Network) para generar contenido periodístico de calidad,
con monitoreo activo de sesgos y verificación de hechos.

FUNDAMENTACIÓN TEÓRICA COMPLETA:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. PLANIFICACIÓN HTN (Russell & Norvig, Cap. 11.3)
   - Descomposición jerárquica de "Producir Noticia" en subtareas
   - Tareas primitivas (buscar, analizar, escribir) y compuestas (gestión)
   - Permite orden parcial: algunos pasos pueden paralelizarse

2. VIGILANCIA DE EJECUCIÓN (AIMA Cap. 12.5)
   - El Analista actúa como "monitor" que verifica precondiciones
   - Si detecta sesgo/error → trigger replanificación (backtracking)
   - Implementa bucle de retroalimentación (similar a sistemas de control)

3. ARQUITECTURA MULTIAGENTE (AIMA Cap. 17)
   - Agentes cooperativos con objetivos compartidos
   - Comunicación mediante paso de artefactos (Task Outputs)
   - Coordinación jerárquica (Manager delega, no negocia)

4. MANEJO DE INCERTIDUMBRE (AIMA Cap. 12.6)
   - Fuentes web pueden ser no confiables → requiere validación
   - Iteración hasta alcanzar umbral de calidad (max_iterations)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from typing import List, Dict, Any
import logging

# Importaciones locales
from src.llm_config import (
    get_investigator_llm,
    get_analyst_llm,
    get_writer_llm,
    get_manager_llm,
)
from src.tools import get_news_search_tool
from src.callbacks import get_callback_handler

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()


# =============================================================================
# DEFINICIÓN DE AGENTES
# =============================================================================


def create_investigator_agent(current_date: str = "") -> Agent:
    """
    AGENTE: Investigador (The Watchdog)

    TEORÍA (AIMA Cap. 16 - Agentes de Recopilación de Información):
    - Rol: Sensor del sistema. Busca información en el entorno (web).
    - Objetivo: Maximizar relevancia y diversidad de fuentes.
    - Características:
      * Alta curiosidad (explorativo)
      * Crítico con fuentes (verifica URLs, dominios)
      * Meticuloso en detalles
      * **NUEVO: Consciencia temporal (grounding temporal)**

    DISEÑO:
    - Temperature baja (0.3) para precisión
    - Herramienta: NewsSearchTool para acceder a ScraperRalf
    - NO toma decisiones editoriales, solo recopila
    - **NUEVO: Recibe fecha actual para filtrar información obsoleta**
    
    Args:
        current_date: Fecha actual para contexto temporal (YYYY-MM-DD)
    """
    # Obtener fecha actual si no se provee
    if not current_date:
        from datetime import datetime
        current_date = datetime.now().strftime("%Y-%m-%d")
    
    # Calcular umbral de antigüedad (hace 24 meses)
    from datetime import datetime, timedelta
    threshold_date = (datetime.strptime(current_date, "%Y-%m-%d") - timedelta(days=730)).strftime("%Y-%m-%d")
    
    return Agent(
        role="Investigador de Noticias Senior con Consciencia Temporal",
        goal=(
            f"📅 CONTEXTO TEMPORAL CRÍTICO:\n"
            f"HOY ES: {current_date}\n"
            f"UMBRAL DE ANTIGÜEDAD: {threshold_date} (hace 24 meses)\n\n"
            f"⚠️ REGLA CRÍTICA: NO PUEDES usar conocimiento previo del modelo o inventar información. "
            "DEBES llamar OBLIGATORIAMENTE a la herramienta 'news_search' y esperar su respuesta completa. "
            "Si no recibes respuesta de la herramienta, reporta ERROR en lugar de inventar datos.\n\n"
            "🎯 OBJETIVO PRINCIPAL:\n"
            "Buscar y recopilar información VERIFICABLE, ACTUAL y DIVERSA de fuentes confiables "
            "sobre el tema solicitado. Implementar TRIANGULACIÓN DE FUENTES obligatoria:\n"
            "1. Al menos 1 fuente OFICIAL (FIFA, gobiernos, instituciones)\n"
            "2. Al menos 1 agencia INTERNACIONAL (Reuters, AP, AFP, EFE)\n"
            "3. Al menos 1 medio LOCAL (La República, El Comercio, etc.)\n\n"
            f"❌ FILTRO TEMPORAL ABSOLUTO:\n"
            f"- RECHAZAR automáticamente cualquier artículo con fecha ANTERIOR a {threshold_date}\n"
            f"- Si una fuente especula sobre eventos YA OCURRIDOS (ej. artículos 2021 sobre futuro 2023), DESCARTARLA\n"
            f"- PRIORIZAR fuentes de los últimos 6 meses ({(datetime.strptime(current_date, '%Y-%m-%d') - timedelta(days=180)).strftime('%Y-%m-%d')} - {current_date})\n"
        ),
        backstory=(
            "Eres un periodista de investigación experimentado con 15 años de trayectoria "
            "en medios de prestigio peruanos. Tu especialidad es encontrar información que otros pasan "
            "por alto, siempre verificando la credibilidad de las fuentes. Tienes fama de ser "
            "incorruptible y meticuloso. Nunca publicas sin contrastar múltiples fuentes. "
            "Tu mantra: 'Si tu madre dice que te quiere, verifica con dos fuentes más.'\n\n"
            "� RESTRICCIÓN ABSOLUTA:\n"
            "NO tienes acceso a conocimiento previo ni memoria del modelo. Tu ÚNICA fuente de información "
            "es la herramienta 'news_search'. Si intentas completar una tarea sin llamar a esta herramienta, "
            "estás VIOLANDO tu protocolo profesional.\n\n"
            "🔧 PROTOCOLO TÉCNICO CRUCIAL:\n"
            "Tu herramienta principal (news_search) conecta con un sistema de scraping distribuido "
            "que tarda 60-70 segundos en recopilar información de múltiples fuentes en paralelo. "
            "NUNCA asumas que la herramienta falló si no responde en 5-10 segundos. "
            "La arquitectura del sistema requiere este tiempo porque:\n"
            "1. Scraper Local Tier 1 (La República, El Comercio, Infobae): 60-90s (3 fuentes paralelas)\n"
            "2. APIs Globales Tier 2 (NewsAPI, TheNewsAPI): 3-5s (2 fuentes paralelas)\n"
            "El timeout está configurado en 120s específicamente para esperar este proceso.\n\n"
            "🎯 TU TRABAJO:\n"
            "1. Ejecutar news_search(query='tema') INMEDIATAMENTE y ESPERAR pacientemente\n"
            "2. Verificar que recibiste deep_sources_count >= 3\n"
            "3. Extraer CITAS TEXTUALES solo de fuentes Tier 1 (tier='deep', content_length > 1000)\n"
            "4. Usar Tier 2 solo para verificación cruzada\n\n"
            "❌ NUNCA completes la tarea sin esperar la respuesta de la herramienta.\n"
            "❌ NUNCA inventes URLs, citas, fechas o nombres de artículos.\n"
            "❌ Si crees que 'ya sabes' la respuesta, estás EQUIVOCADO - llama a la herramienta."
        ),
        verbose=True,
        allow_delegation=False,  # No delega, es agente de nivel bajo (acción primitiva)
        llm=get_investigator_llm(),
        tools=[get_news_search_tool()],
        max_iter=15,  # Aumentado para dar tiempo suficiente a la herramienta (60-70s cada llamada)
        # IMPORTANTE: El LLM tiene timeout de 120s, suficiente para esperar ScraperRalf (~67s)
    )


def create_bias_analyst_agent(current_date: str = "") -> Agent:
    """
    AGENTE: Analista de Sesgos (The Critic)

    TEORÍA (AIMA Cap. 12.5 - Vigilancia de Ejecución):
    - Rol: Monitor de calidad. Verifica precondiciones de "noticia válida".
    - Objetivo: Detectar sesgos, falacias lógicas, datos no verificados.
    - Implementa "Verificación de Precondiciones" antes de permitir publicación.

    PRECONDICIONES QUE VERIFICA:
    1. Neutralidad (ausencia de lenguaje cargado emocionalmente)
    2. Falacias lógicas (ad hominem, falsa dicotomía, etc.)
    3. Datos sin fuente (afirmaciones no respaldadas)
    4. Balance de perspectivas (no unilateral)

    DISEÑO:
    - Temperature media (0.5) para balance rigor/flexibilidad
    - NO tiene herramientas (trabaja con texto, no con mundo externo)
    - Puede solicitar RE-búsqueda si detecta problemas

    Args:
        current_date: Fecha actual para contexto temporal (YYYY-MM-DD)
    """
    if current_date is None:
        from datetime import datetime

        current_date = datetime.now().strftime("%Y-%m-%d")

    return Agent(
        role="Analista de Sesgos y Fact-Checker",
        goal=(
            f"Analizar críticamente el contenido recopilado para detectar sesgos, "
            f"falacias lógicas, información no verificada o desequilibrio de perspectivas. "
            f"Aprobar solo contenido que cumpla estándares periodísticos de calidad. "
            f"En caso de encontrar problemas, especificar exactamente qué se debe corregir. "
            f"\n\n⚠️ CONTEXTO TEMPORAL CRÍTICO: HOY ES {current_date}. "
            f"Cualquier noticia fechada en o antes de {current_date} es VÁLIDA y del PRESENTE. "
            f"NO rechaces noticias por 'anomalías temporales' o 'ser del futuro' si están fechadas <= {current_date}."
        ),
        backstory=(
            f"📅 FECHA ACTUAL: {current_date} - Esta es la realidad temporal en la que trabajas.\n\n"
            f"Eres un académico con doctorado en Filosofía del Lenguaje y especialización en "
            f"Pensamiento Crítico. Has trabajado como ombudsman en grandes medios, detectando "
            f"sesgos sutiles que otros no ven. Conoces todas las falacias lógicas de memoria "
            f"y puedes identificar lenguaje manipulador a kilómetros de distancia. Tu reputación "
            f"es de ser implacable pero justo. No permites que nada pase sin verificación rigurosa, "
            f"pero tampoco bloqueas contenido injustificadamente. Tu norte: la verdad objetiva.\n\n"
            f"⚠️ IMPORTANTE: Cuando evalúes fechas de noticias, recuerda que HOY es {current_date}. "
            f"No confundas fechas recientes con 'predicciones del futuro'. Si un artículo está fechado "
            f"en {current_date} o antes, es información del presente o pasado reciente."
        ),
        verbose=True,
        allow_delegation=False,
        llm=get_analyst_llm(),
        tools=[],  # Agente puramente analítico, no necesita herramientas externas
    )


def create_writer_agent() -> Agent:
    """
    AGENTE: Redactor (The Writer)

    TEORÍA (AIMA Cap. 23 - Procesamiento de Lenguaje Natural):
    - Rol: Efector del sistema. Genera el producto final (texto).
    - Objetivo: Comunicar información de forma clara, atractiva y neutral.
    - Implementa "Generación de Lenguaje Natural" (NLG)

    CARACTERÍSTICAS:
    - Alta creatividad para engagement, pero restringida por hechos
    - Sigue estructura periodística (pirámide invertida)
    - Adapta tono según audiencia

    DISEÑO:
    - Temperature alta (0.8) para creatividad en redacción
    - Solo escribe si el Analista aprueba (precondición)
    - Formatea según estándares editoriales
    """
    return Agent(
        role="Redactor Senior",
        goal=(
            "Redactar un artículo periodístico profesional en formato Markdown bien estructurado. "
            "Basarte EXCLUSIVAMENTE en los hechos validados por el Analista de Sesgos. "
            "Usar estructura de pirámide invertida (información más importante primero), "
            "lenguaje claro y neutral, y titular atractivo pero honesto. "
            "\n\n📝 FORMATO REQUERIDO - MARKDOWN ESTRUCTURADO:\n"
            "1. Titular principal (# H1) - Conciso y directo\n"
            "2. Subtítulo explicativo (## H2) - Contexto adicional\n"
            "3. Lead/Entradilla (párrafo inicial en **negrita**) - Resume los 5W+H\n"
            "4. Cuerpo dividido en secciones con subtítulos (## H2 o ### H3)\n"
            "5. Citas textuales formateadas como blockquotes (> texto)\n"
            "6. Datos importantes destacados en **negrita**\n"
            "7. Listas para enumeraciones (- item)\n"
            "8. Conclusión o cierre (## Conclusión)\n\n"
            "⚠️ IMPORTANTE: El artículo debe ser legible en Markdown Y renderizar bien en HTML."
        ),
        backstory=(
            "Eres un redactor galardonado con múltiples premios de periodismo digital. "
            "Tu especialidad es crear contenido que funciona tanto en formato impreso como digital. "
            "Dominas Markdown a la perfección y sabes estructurar artículos para máxima legibilidad. "
            "Has escrito para The New York Times, The Guardian y El País. "
            "Tu estilo es limpio, directo y elegante. Usas subtítulos efectivos, destacas datos clave "
            "en negrita, y formateas citas textuales como blockquotes para darles impacto visual. "
            "Jamás sacrificas la precisión por el estilo. Tu lema: "
            "'La mejor historia es la que está bien contada, bien formateada Y es verdad.'\n\n"
            "📐 TU PLANTILLA MENTAL PARA ARTÍCULOS:\n"
            "# [Titular Impactante]\n"
            "## [Subtítulo que amplía contexto]\n\n"
            "**[Lead en negrita: Qué pasó, quién, dónde, cuándo, por qué]**\n\n"
            "## Los Hechos\n"
            "[Desarrollo cronológico o temático]\n\n"
            '> "[Cita textual importante]" - [Fuente]\n\n'
            "### Dato Clave\n"
            "- **Cifra importante**: Contexto\n"
            "- **Otra cifra**: Explicación\n\n"
            "## Contexto\n"
            "[Background necesario para entender]\n\n"
            "## Conclusión\n"
            "[Cierre que resume impacto o próximos pasos]"
        ),
        verbose=True,
        allow_delegation=False,
        llm=get_writer_llm(),
        tools=[],  # El redactor solo escribe, no busca información
    )


def create_editor_agent() -> Agent:
    """
    AGENTE: Jefe de Redacción (The Manager)

    TEORÍA (AIMA Cap. 11.3 - Planificación HTN):
    - Rol: Planificador jerárquico. Descompone "Producir Noticia" en tareas.
    - Implementa descomposición de tareas compuestas en primitivas.
    - Coordina la ejecución (no hace trabajo directo, delega).

    PLAN HTN:
    1. TAREA COMPUESTA: Producir Noticia(tema)
       ├── PRIMITIVA: Buscar Información(tema)         → Investigador
       ├── PRIMITIVA: Validar Calidad(info)            → Analista
       │   ├── SI error → REPLANIFICAR (volver a 1)
       │   └── SI OK → continuar
       └── PRIMITIVA: Redactar Artículo(info_validada) → Redactor

    DISEÑO:
    - Temperature balanceada (0.6)
    - Puede delegar a otros agentes (allow_delegation=True)
    - Toma decisiones de alto nivel (qué tarea sigue)
    """
    return Agent(
        role="Jefe de Redacción",
        goal=(
            "Orquestar el proceso completo de producción de noticias, delegando tareas "
            "a especialistas y asegurando que el producto final cumpla los más altos "
            "estándares periodísticos. Tomar decisiones sobre qué información priorizar "
            "y cuándo re-investigar si la calidad no es suficiente."
        ),
        backstory=(
            "Eres el jefe de redacción de un medio de prestigio internacional con 25 años "
            "de experiencia. Has dirigido coberturas ganadoras de Pulitzer y sabes reconocer "
            "una buena historia cuando la ves. Tu habilidad principal es coordinar equipos "
            "diversos y extraer lo mejor de cada periodista. Eres exigente pero justo, "
            "y sabes cuándo insistir en más investigación y cuándo publicar. Tu reputación "
            "es de ser un líder que nunca compromete la calidad por la velocidad."
        ),
        verbose=True,
        allow_delegation=True,  # CRÍTICO: permite coordinación HTN
        llm=get_manager_llm(),
        tools=[],  # El manager no ejecuta, solo coordina
    )


# =============================================================================
# DEFINICIÓN DE TAREAS (HTN - DESCOMPOSICIÓN JERÁRQUICA)
# =============================================================================


def create_investigation_task(agent: Agent, topic: str, current_date: str) -> Task:
    """
    TAREA PRIMITIVA: Recolección de Información

    TEORÍA (AIMA Cap. 11.2):
    - Acción primitiva: no se puede descomponer más
    - Precondiciones: Tema válido, herramienta ScraperRalf disponible
    - Efectos: Genera contexto con información cruda

    Args:
        agent: Investigador que ejecuta la tarea
        topic: Tema a investigar
        current_date: Fecha actual para contexto temporal (YYYY-MM-DD)
    """
    # Calcular umbral de antigüedad (hace 24 meses)
    from datetime import datetime, timedelta
    threshold_date = (datetime.strptime(current_date, "%Y-%m-%d") - timedelta(days=730)).strftime("%Y-%m-%d")
    recent_threshold = (datetime.strptime(current_date, "%Y-%m-%d") - timedelta(days=180)).strftime("%Y-%m-%d")
    
    return Task(
        description=(
            f"⚠️ CONTEXTO TEMPORAL IMPORTANTE:\n"
            f"HOY ES: {current_date}\n"
            f"Cualquier noticia con fecha <= {current_date} es REAL y VÁLIDA.\n"
            f"NO rechaces noticias por 'ser del futuro' - {current_date} es HOY.\n\n"
            f"🎯 TAREA: Investigar exhaustivamente el tema: '{topic}'\n\n"
            f"{'='*80}\n"
            f"🚨 PROTOCOLO OBLIGATORIO - NO SALTARSE NINGÚN PASO\n"
            f"{'='*80}\n\n"
            f"PASO 1: LLAMAR A LA HERRAMIENTA\n"
            f"   ➤ DEBES ejecutar: news_search(query='{topic}')\n"
            f"   ➤ NO continúes sin hacer esta llamada\n"
            f"   ➤ NO inventes datos ni uses conocimiento previo\n\n"
            f"PASO 2: ESPERAR PACIENTEMENTE (60-70 SEGUNDOS)\n"
            f"   ➤ La herramienta ScraperRalf tarda entre 60-70 segundos\n"
            f"   ➤ Verás el mensaje: 'Tool Called: news_search'\n"
            f"   ➤ ESPERA hasta ver: 'Tool Response: {{...}}'\n"
            f"   ➤ La respuesta NO llega por streaming - viene TODO junto\n"
            f"   ➤ Si crees que ya terminó a los 5-10s, ES INCORRECTO - sigue esperando\n\n"
            f"PASO 3: VERIFICAR QUE RECIBISTE DATOS COMPLETOS\n"
            f"   ➤ La respuesta debe tener campo 'status': 'success'\n"
            f"   ➤ Debe contener 'deep_sources_count' >= 3 (mínimo)\n"
            f"   ➤ Si deep_sources_count = 0, hubo timeout - REPORTARLO\n\n"
            f"PASO 4: SOLO ENTONCES procesar los datos\n\n"
            f"{'='*80}\n"
            f"❌ ESTÁ PROHIBIDO:\n"
            f"{'='*80}\n"
            f"✗ Completar la tarea sin llamar a la herramienta\n"
            f"✗ Terminar antes de los 60 segundos\n"
            f"✗ Usar datos inventados o conocimiento general\n"
            f"✗ Decir 'no encontré información' sin esperar la respuesta\n\n"
            f"Usar la herramienta de búsqueda para encontrar al menos 3 artículos "
            f"de fuentes diferentes. Para cada fuente, verificar:\n"
            f"1. Credibilidad del medio (evitar blogs sin reputación)\n"
            f"2. Actualidad de la información (preferir últimas 48h)\n"
            f"3. Presencia de datos verificables (estadísticas, quotes, etc.)\n\n"
            f"ESTRATEGIA DE FUENTES:\n"
            f"La herramienta de búsqueda retorna 2 tipos de fuentes:\n\n"
            f"🟢 TIER 1 (FUENTES PROFUNDAS) - Prioridad ALTA:\n"
            f"   - La República, El Comercio, Infobae\n"
            f"   - Identificables por: tier='deep', content_length > 1000\n"
            f"   - Contienen artículos COMPLETOS con citas textuales\n"
            f"   - USAR ESTAS para extraer quotes, estadísticas, declaraciones\n\n"
            f"🟡 TIER 2 (APIs GLOBALES) - Para verificación cruzada:\n"
            f"   - NewsAPI, TheNewsAPI\n"
            f"   - Identificables por: tier='api', content_length < 500\n"
            f"   - Contienen snippets/resúmenes truncados\n"
            f"   - USAR ESTAS solo para confirmar que la noticia existe internacionalmente\n\n"
            f"VERIFICACIÓN DE COMPLETITUD:\n"
            f"Antes de entregar tu informe, confirma que:\n"
            f"- Recibiste al menos 3 artículos Tier 1 (deep_sources_count >= 3)\n"
            f"- El campo 'status' de la respuesta es 'success'\n"
            f"- Si deep_sources_count es 0, significa que hubo un problema de timeout\n\n"
            f"🔍 SANITY CHECK FINAL (OBLIGATORIO):\n"
            f"Antes de finalizar, LEE TODO tu informe y verifica:\n\n"
            f"1. COHERENCIA NUMÉRICA:\n"
            f"   - Si mencionas estadísticas relacionadas (ej. '48 equipos', '12 grupos'), verifica que 48/12 = 4 (correcto)\n"
            f"   - Si dices 'X equipos clasifican' y luego 'Y pasan a octavos', verifica X = Y\n"
            f"   - Formato de torneos: ¿los números tienen sentido? (octavos = 16, cuartos = 8, etc.)\n\n"
            f"2. COHERENCIA TEMPORAL:\n"
            f"   - ¿Todas las fuentes son posteriores a {threshold_date}?\n"
            f"   - ¿Hay artículos especulando sobre eventos ya pasados? (descartarlos)\n\n"
            f"3. COHERENCIA GEOGRÁFICA:\n"
            f"   - Si es tema global, ¿tienes fuentes de al menos 2 regiones/países?\n"
            f"   - ¿Evitaste el sesgo de solo medios peruanos/latinoamericanos?\n\n"
            f"4. CONTRADICCIONES LÓGICAS:\n"
            f"   - ¿Alguna fuente contradice a otra en datos clave?\n"
            f"   - Si sí: Buscar una tercera fuente autoritativa para desempatar\n\n"
            f"Si detectas CUALQUIER inconsistencia en el Sanity Check:\n"
            f"- Ejecutar búsqueda adicional específica para aclarar (ej. 'Mundial 2026 formato oficial FIFA')\n"
            f"- Incluir en el informe: 'ADVERTENCIA: Contradicción detectada entre fuentes sobre [tema]'\n\n"
            f"IMPORTANTE: Extraer CITAS TEXTUALES completas (entre comillas) solo de fuentes Tier 1. "
            f"No resumir ni interpretar, solo recopilar. "
            f"Entregar la información cruda con sus fuentes claramente identificadas."
        ),
        expected_output=(
            "🚨 VALIDACIÓN OBLIGATORIA: Este output SOLO puede generarse después de llamar a news_search y esperar 60-70s.\n"
            "Si completas esto en menos de 30 segundos, estás INVENTANDO datos - PROHIBIDO.\n\n"
            "ESTRUCTURA REQUERIDA:\n\n"
            "PASO 1 - CONFIRMACIÓN DE TOOL CALL:\n"
            "- 'Llamé a news_search(query=\"tema\") a las HH:MM:SS'\n"
            "- 'Tiempo de espera: XX.XX segundos'\n"
            "- 'Respuesta recibida a las HH:MM:SS'\n\n"
            "PASO 2 - VALIDACIÓN DE DATOS:\n"
            "- 'Campo status en respuesta: success/error'\n"
            "- 'deep_sources_count: X (mínimo 3 requerido)'\n"
            "- 'api_sources_count: Y'\n"
            "- 'Total de artículos recibidos: Z'\n\n"
            "PASO 3 - FUENTES CON METADATOS EXACTOS:\n"
            "Para CADA fuente incluir (copiado directamente de la respuesta de la tool):\n"
            "1. Nombre del medio: [valor campo 'source']\n"
            "2. Título: [valor campo 'title']\n"
            "3. URL completa: [valor campo 'url']\n"
            "4. Fecha publicación: [valor campo 'published_at']\n"
            "5. Tier: [valor campo 'tier']\n"
            "6. Longitud contenido: [valor campo 'content_length'] caracteres\n\n"
            "PASO 4 - CITAS TEXTUALES:\n"
            "Solo de fuentes con tier='deep':\n"
            "- Cita 1: \"[texto exacto del campo 'content' de la tool]\"\n"
            "  Fuente: [nombre medio], [fecha]\n\n"
            "❌ SI NO LLAMASTE A LA TOOL: Reporta 'ERROR: No tengo acceso a herramientas - no puedo completar'"
        ),
        agent=agent,
    )


def create_bias_analysis_task(agent: Agent, context_task: Task) -> Task:
    """
    TAREA PRIMITIVA: Análisis de Sesgos

    TEORÍA (AIMA Cap. 12.5 - Vigilancia de Ejecución):
    - Verifica precondiciones antes de permitir avance
    - Si falla verificación → requiere replanificación
    - Implementa bucle de retroalimentación (feedback loop)

    PRECONDICIONES VERIFICADAS:
    1. Al menos 2 fuentes independientes
    2. Ausencia de lenguaje emocional cargado
    3. No hay falacias lógicas evidentes
    4. Balance de perspectivas (si es tema controversial)

    Args:
        agent: Analista de Sesgos
        context_task: Tarea anterior (investigación) de la que depende
    """
    return Task(
        description=(
            "Analizar críticamente el informe del Investigador. Ejecutar las siguientes verificaciones:\n\n"
            "1. VERIFICACIÓN DE FALACIAS LÓGICAS:\n"
            "   - Ad hominem, falsa dicotomía, pendiente resbaladiza, etc.\n"
            "   - Generalización apresurada basada en casos aislados\n\n"
            "2. DETECCIÓN DE SESGOS:\n"
            "   - Lenguaje emocional o valorativo\n"
            "   - Selección sesgada de fuentes (solo un lado de la historia)\n"
            "   - Omisión de información relevante que contradiga narrativa\n\n"
            "3. VERIFICACIÓN DE HECHOS:\n"
            "   - ¿Todas las afirmaciones tienen fuente?\n"
            "   - ¿Las fuentes son creíbles y verificables?\n"
            "   - ¿Hay contradicciones entre fuentes?\n\n"
            "4. EVALUACIÓN DE BALANCE:\n"
            "   - Si es tema controversial, ¿se presentan múltiples perspectivas?\n"
            "   - ¿Se da contexto suficiente?\n\n"
            "5. VALIDACIÓN DE COHERENCIA MATEMÁTICA Y LÓGICA (NUEVO):\n"
            "   - Si hay estadísticas relacionadas, ¿son coherentes? (ej. '48 equipos / 12 grupos = 4 por grupo')\n"
            "   - Si se mencionan fases de torneo, ¿los números cuadran? (octavos=16, cuartos=8, semis=4, final=2)\n"
            "   - ¿Hay contradicciones temporales? (ej. artículo de 2021 especulando sobre 2023)\n"
            "   - ¿Hay datos que desafían la física/lógica? (velocidades imposibles, fechas futuras, etc.)\n\n"
            "6. TRIANGULACIÓN DE FUENTES (NUEVO):\n"
            "   - ¿Hay al menos 1 fuente oficial/autoritativa?\n"
            "   - ¿Hay al menos 1 fuente internacional para temas globales?\n"
            "   - Si el tema es global y solo hay fuentes locales → RECHAZAR por sesgo geográfico\n\n"
            "7. VERIFICACIÓN TEMPORAL:\n"
            "   - ¿Las fuentes son recientes (últimos 24 meses preferentemente)?\n"
            "   - ¿Hay fuentes obsoletas tratando de predecir eventos ya ocurridos?\n\n"
            "Si detectas problemas GRAVES (más de 2 issues críticos), especifica exactamente:\n"
            "- Qué está mal\n"
            "- Qué información adicional se necesita\n"
            "- Sugerencias de búsquedas alternativas\n\n"
            "EJEMPLOS DE RECHAZO OBLIGATORIO:\n"
            "❌ 'Solo fuentes peruanas/argentinas sobre tema global (Mundial FIFA)'\n"
            "   → Requiere: Buscar fuentes de FIFA.com, Reuters, AP\n"
            "❌ 'Contradicción: 12 grupos → 24 clasifican, pero dice octavos de 16'\n"
            "   → Requiere: Buscar 'formato oficial Mundial 2026 FIFA'\n"
            "❌ 'Fuentes de 2021 especulando sobre campeón 2022 (ya ocurrió)'\n"
            "   → Requiere: Buscar 'campeón Mundial 2022 resultado final'\n\n"
            "Si la calidad es aceptable, da luz verde explícita para redacción."
        ),
        expected_output=(
            "Reporte de análisis con:\n"
            "- VEREDICTO: APROBADO / REQUIERE CORRECCIONES / RECHAZADO\n"
            "- Lista de problemas encontrados (si los hay) con severidad\n"
            "- Validación matemática/lógica de estadísticas clave\n"
            "- Evaluación de triangulación de fuentes (oficial + internacional + local)\n"
            "- Verificación temporal de fuentes (antigüedad)\n"
            "- Recomendaciones específicas de corrección\n"
            "- Hechos validados listos para redacción (si se aprueba)\n"
            "- Justificación de la decisión"
        ),
        agent=agent,
        context=[context_task],  # CRÍTICO: Depende del output del Investigador
    )


def create_writing_task(agent: Agent, context_tasks: List[Task]) -> Task:
    """
    TAREA PRIMITIVA: Redacción del Artículo

    TEORÍA (AIMA Cap. 23 - Generación de Lenguaje Natural):
    - Transforma representación estructurada en texto fluido
    - Respeta precondiciones (solo hechos validados por Analista)

    ESTRUCTURA REQUERIDA (Pirámide Invertida):
    1. Título (captura esencia, max 10 palabras)
    2. Lead (primer párrafo: quién, qué, cuándo, dónde, por qué)
    3. Cuerpo (detalles en orden decreciente de importancia)
    4. Contexto/Background
    5. Conclusión (opcional, solo si aporta cierre)

    Args:
        agent: Redactor
        context_tasks: Tareas anteriores (investigación y análisis)
    """
    return Task(
        description=(
            "🎯 OBJETIVO: Redactar un artículo periodístico profesional de alta calidad tipo revista digital, "
            "usando ÚNICAMENTE los hechos validados por el Analista de Sesgos.\n\n"
            "═══════════════════════════════════════════════════════════════\n"
            "📰 PLANTILLA OBLIGATORIA - FORMATO MARKDOWN TIPO REVISTA\n"
            "═══════════════════════════════════════════════════════════════\n\n"
            "⚠️ CRÍTICO - REGLA DE SALTOS DE LÍNEA:\n"
            "- CADA header (#, ##, ###) DEBE tener UNA LÍNEA VACÍA ANTES Y DESPUÉS\n"
            "- Ejemplo CORRECTO:\n"
            "  Párrafo anterior.\n"
            "  \n"
            "  ## Título de Sección\n"
            "  \n"
            "  Párrafo siguiente.\n"
            "- Ejemplo INCORRECTO: 'texto## Título' (SIN saltos de línea)\n\n"
            "# TÍTULO IMPACTANTE Y CLARO (Máximo 12 palabras)\n\n"
            "**[LEAD EN NEGRITA]: Primer párrafo que resume toda la historia en 2-3 oraciones contundentes. "
            "Responde: ¿Qué pasó? ¿Quién? ¿Dónde? ¿Cuándo? ¿Por qué importa? Este párrafo DEBE estar en negrita.**\n\n"
            "## Contexto e Introducción\n\n"
            "Primer párrafo desarrollando el contexto general. Presenta el tema sin entrar todavía en detalles específicos. "
            "Establece el escenario con datos verificables.\n\n"
            "Segundo párrafo conectando con la actualidad o explicando la relevancia del tema ahora.\n\n"
            '> "Las citas textuales de expertos, protagonistas o fuentes oficiales van aquí en blockquotes. '
            'Esto da autoridad y credibilidad al artículo."\n'
            "> — Nombre Apellido, Cargo/Institución\n\n"
            "## Desarrollo Principal del Tema\n\n"
            "### Primer Aspecto Clave\n\n"
            "Análisis profundo del primer punto importante con evidencias concretas:\n\n"
            "- **Dato verificable 1**: Contexto y fuente\n"
            "- **Dato verificable 2**: Impacto y consecuencias\n"
            "- **Dato verificable 3**: Relación con el tema general\n\n"
            "Párrafo explicativo conectando los puntos con análisis crítico.\n\n"
            "### Segundo Aspecto Clave\n\n"
            "Desarrollo del segundo punto relevante con evidencias sólidas y datos estadísticos, estudios o informes. "
            "**Enfatiza conceptos clave en negrita** para facilitar lectura rápida.\n\n"
            "### Tercer Aspecto (si aplica)\n\n"
            "Continúa el análisis con profundidad periodística y datos verificables.\n\n"
            "---\n\n"
            "## Análisis de Credibilidad y Sesgos\n\n"
            "Evaluación crítica de las fuentes utilizadas:\n\n"
            "1. **Sesgos detectados**: Qué perspectivas podrían estar sobre-representadas\n"
            "2. **Fuentes confiables**: Balance entre Tier 1, Tier 2 y advertencias\n"
            "3. **Advertencias**: Información que requiere verificación adicional\n\n"
            '> "Si hay advertencias importantes sobre la fiabilidad de cierta información, '
            'inclúyelas aquí como blockquote destacado."\n\n'
            "## Implicaciones y Consecuencias\n\n"
            "Análisis del impacto real: ¿Qué significa esto? ¿A quién afecta?\n\n"
            "- Consecuencias a corto plazo\n"
            "- Implicaciones a largo plazo\n"
            "- Grupos o sectores afectados\n\n"
            "## Conclusión\n\n"
            "Síntesis de los puntos principales sin repetir el lead. Cierra con perspectivas sobre el futuro "
            "o una reflexión relevante que invite a seguir pensando en el tema.\n\n"
            "---\n\n"
            "**Fuentes principales**: Lista de medios y documentos consultados\n\n"
            "═══════════════════════════════════════════════════════════════\n"
            "✅ CHECKLIST DE CALIDAD OBLIGATORIO\n"
            "═══════════════════════════════════════════════════════════════\n\n"
            "ESTRUCTURA:\n"
            "✓ UN SOLO título H1 (#)\n"
            "✓ Lead en negrita al inicio (2-3 oraciones)\n"
            "✓ Mínimo 4 secciones H2 (##)\n"
            "✓ Subsecciones H3 (###) para desglosar temas complejos\n"
            "✓ Conclusión clara al final\n\n"
            "FORMATO MARKDOWN:\n"
            "✓ Citas importantes en > blockquotes con atribución\n"
            "✓ Listas con - viñetas o 1. numeradas\n"
            "✓ **Negrita** solo para términos clave (no abusar)\n"
            "✓ *Cursiva* ocasionalmente para énfasis sutil\n"
            "✓ Separadores --- si cambias de tema drásticamente\n"
            "✓ Párrafos separados con línea en blanco\n\n"
            "CONTENIDO:\n"
            "✓ Basado en hallazgos verificados de investigación\n"
            "✓ Incluye análisis de sesgos integrado naturalmente\n"
            "✓ Tono periodístico profesional (ni académico ni sensacionalista)\n"
            "✓ Longitud: 900-1400 palabras\n"
            "✓ Sin opiniones personales, solo hechos y análisis\n\n"
            "ESTILO:\n"
            "✓ Párrafos de 3-5 oraciones (legibilidad)\n"
            "✓ Transiciones suaves entre secciones\n"
            "✓ Lenguaje claro y directo\n"
            "✓ Evita jerga técnica excesiva\n"
            "✓ Si usas términos especializados, explícalos\n\n"
            "═══════════════════════════════════════════════════════════════\n"
            "❌ PROHIBIDO ABSOLUTAMENTE\n"
            "═══════════════════════════════════════════════════════════════\n\n"
            "✗ Múltiples H1 (# Título) - solo uno\n"
            "✗ Lead sin negrita o débil\n"
            "✗ Párrafos de una sola oración\n"
            "✗ Olvidar separar párrafos con línea en blanco\n"
            "✗ Poner headers sin saltos de línea (texto## Header es INCORRECTO)\n"
            "✗ Usar blockquotes para texto normal (solo citas)\n"
            "✗ Abusar de negritas o cursivas\n"
            "✗ Conclusiones vagas o genéricas\n"
            "✗ Opiniones personales o especulación\n"
            "✗ Datos no verificados por el Analista\n"
            "✗ Lenguaje sensacionalista\n\n"
            "TONO DE REFERENCIA: The New York Times, El País, The Guardian, Le Monde"
        ),
        expected_output=(
            "Artículo periodístico completo en Markdown con formato de revista profesional:\n\n"
            "✓ Título H1 impactante\n"
            "✓ Lead en negrita (2-3 oraciones contundentes)\n"
            "✓ Mínimo 4 secciones H2 con nombres descriptivos\n"
            "✓ Subsecciones H3 organizando subtemas\n"
            "✓ 2-3 blockquotes con citas relevantes y atribución\n"
            "✓ Listas con viñetas para datos clave\n"
            "✓ Negrita estratégica en conceptos importantes\n"
            "✓ Sección de análisis de sesgos integrada\n"
            "✓ Conclusión sólida con perspectivas\n"
            "✓ Pie con fuentes principales\n"
            "✓ Longitud: 900-1400 palabras\n"
            "✓ Tono periodístico profesional y objetivo\n"
            "✓ Formato Markdown impecable que se renderizará hermosamente en el frontend"
        ),
        agent=agent,
        context=context_tasks,  # Depende de investigación Y análisis
    )


# =============================================================================
# ENSAMBLAJE DE LA CREW (PROCESO HTN)
# =============================================================================


class NewsCrew:
    """
    Orquestador principal del sistema multiagente.

    TEORÍA (AIMA Cap. 17.4 - Arquitecturas de Agentes):
    - Implementa arquitectura jerárquica (Manager-Worker)
    - Proceso: Process.hierarchical → Coordinación top-down
    - Comunicación: Paso de artefactos (no comunicación directa)

    FLUJO DE EJECUCIÓN:
    1. Manager recibe objetivo global
    2. Manager descompone en tareas (HTN)
    3. Asigna Investigador → espera resultado
    4. Asigna Analista (con contexto de Investigador) → espera resultado
    5. SI Analista rechaza → REPLANIFICAR (volver a 3 con nuevos parámetros)
    6. SI Analista aprueba → Asignar Redactor → FIN
    """

    def __init__(self, session_id: str = "default", current_date: str = ""):
        """
        Inicializa la crew con todos sus agentes y callbacks.

        Args:
            session_id: ID de sesión para tracking en frontend
            current_date: Fecha actual para contexto temporal (YYYY-MM-DD)
        """
        # Obtener fecha actual si no se provee
        if not current_date:
            from datetime import datetime
            current_date = datetime.now().strftime("%Y-%m-%d")
        
        self.session_id = session_id
        self.current_date = current_date
        self.callback = get_callback_handler(session_id)

        # Crear agentes con contexto temporal
        self.investigator = create_investigator_agent(current_date)
        self.analyst = create_bias_analyst_agent(current_date)
        self.writer = create_writer_agent()
        self.editor = create_editor_agent()

        logger.info(f"✅ NewsCrew inicializada con 4 agentes (Fecha: {current_date})")

    def create_crew(self, topic: str, current_date: str = "") -> Crew:
        """
        Crea una instancia de Crew con tareas configuradas para un tema.

        Args:
            topic: Tema sobre el que producir la noticia
            current_date: Fecha actual para contexto temporal (YYYY-MM-DD)

        Returns:
            Instancia de Crew lista para ejecutar
        """
        # Crear tareas con dependencias (grafo HTN)
        task_investigate = create_investigation_task(
            self.investigator, topic, current_date
        )
        task_analyze = create_bias_analysis_task(self.analyst, task_investigate)
        task_write = create_writing_task(self.writer, [task_investigate, task_analyze])

        # Notificar inicio al frontend
        self.callback.on_crew_start("NewsCrew", 3)

        # Ensamblar crew - IMPORTANTE: En modo hierarchical, el manager NO se incluye en agents[]
        crew = Crew(
            agents=[self.investigator, self.analyst, self.writer],  # type: ignore
            tasks=[task_investigate, task_analyze, task_write],  # type: ignore
            process=Process.hierarchical,  # type: ignore
            manager_agent=self.editor,  # type: ignore
            verbose=True,  # type: ignore
            max_rpm=10,  # type: ignore
        )

        logger.info(f"🎬 Crew creada para tema: '{topic}'")
        return crew

    def run(self, topic: str, current_date: str = "") -> Dict[str, Any]:
        """
        Ejecuta el proceso completo de producción de noticias CON BUCLE DE RETROALIMENTACIÓN.

        Args:
            topic: Tema a investigar y escribir
            current_date: Fecha actual en formato YYYY-MM-DD. Si None, usa datetime.now()

        Returns:
            Diccionario con resultado y metadata

        TEORÍA (AIMA Cap. 12.5 - Vigilancia de Ejecución):
        - Implementa bucle de retroalimentación: si Analista rechaza → volver a investigar
        - Máximo 3 iteraciones para evitar bucles infinitos
        - Cada iteración refina la búsqueda basándose en feedback del Analista
        """
        # Obtener fecha actual
        if current_date is None:
            from datetime import datetime

            current_date = datetime.now().strftime("%Y-%m-%d")

        MAX_ITERATIONS = 3
        iteration = 0

        try:
            logger.info(f"🚀 Iniciando producción de noticia: '{topic}'")
            logger.info(f"📅 Fecha de referencia: {current_date}")

            while iteration < MAX_ITERATIONS:
                iteration += 1
                logger.info(f"🔄 Iteración {iteration}/{MAX_ITERATIONS}")

                # PASO 1: Investigación
                logger.info("📊 FASE 1: Investigación")
                investigator = create_investigator_agent(current_date)
                task_investigate = create_investigation_task(
                    investigator, topic, current_date
                )

                investigation_crew = Crew(
                    agents=[investigator],
                    tasks=[task_investigate],
                    process=Process.sequential,
                    verbose=True,
                )

                # Registrar callbacks para investigación
                self.callback.on_agent_start(
                    "Investigador de Noticias", f"Investigando: {topic}"
                )
                investigation_result = investigation_crew.kickoff()
                self.callback.on_agent_finish(
                    "Investigador de Noticias", str(investigation_result)
                )

                logger.info(
                    f"✅ Investigación completada: {len(str(investigation_result))} chars"
                )

                # PASO 2: Análisis de Sesgos (PUNTO DE DECISIÓN)
                logger.info("🔍 FASE 2: Análisis de Sesgos")
                logger.info(
                    f"📅 Creando Analista con fecha de referencia: {current_date}"
                )
                print(f"\n{'='*80}")
                print(f"🔍 ANALISTA - FECHA DE CONTEXTO: {current_date}")
                print(f"{'='*80}\n")

                analyst = create_bias_analyst_agent(current_date)

                # Crear tarea de análisis con contexto de investigación
                task_analyze = Task(
                    description=(
                        f"📅 CONTEXTO TEMPORAL: Hoy es {current_date}. Cualquier noticia con fecha ≤ {current_date} es VÁLIDA.\n\n"
                        f"Analizar el siguiente informe de investigación:\n\n{investigation_result}\n\n"
                        "Ejecutar verificaciones de:\n"
                        "1. Falacias lógicas\n"
                        "2. Sesgos de confirmación\n"
                        "3. Verificación de fuentes\n"
                        "4. Balance de perspectivas\n\n"
                        "⚠️ IMPORTANTE sobre fechas:\n"
                        f"- HOY es {current_date}\n"
                        f"- Noticias de {current_date} o anteriores son del PRESENTE/PASADO, NO del futuro\n"
                        f"- NO rechaces noticias por 'anomalías temporales' si están fechadas ≤ {current_date}\n\n"
                        "Tu veredicto DEBE ser uno de estos:\n"
                        "- APROBADO: Calidad suficiente para redacción\n"
                        "- RECHAZADO: Requiere nueva investigación\n\n"
                        "Si rechazas, especifica EXACTAMENTE qué información falta o qué fuentes adicionales se necesitan."
                    ),
                    expected_output=(
                        "VEREDICTO: [APROBADO/RECHAZADO]\n"
                        "PROBLEMAS ENCONTRADOS: [lista]\n"
                        "RECOMENDACIONES: [acciones específicas]\n"
                        "HECHOS VALIDADOS: [si aprobado]"
                    ),
                    agent=analyst,
                )

                analysis_crew = Crew(
                    agents=[analyst],
                    tasks=[task_analyze],
                    process=Process.sequential,
                    verbose=True,
                )

                self.callback.on_agent_start(
                    "Analista de Sesgos y Fact-Checker", "Analizando reporte..."
                )
                analysis_result = analysis_crew.kickoff()
                self.callback.on_agent_finish(
                    "Analista de Sesgos y Fact-Checker", str(analysis_result)
                )

                analysis_text = str(analysis_result).upper()

                # CONDICIONAL CRÍTICO: ¿El Analista aprobó o rechazó?
                if "APROBADO" in analysis_text and "RECHAZADO" not in analysis_text:
                    logger.info(
                        "✅ Analista APROBÓ el contenido - Procediendo a redacción"
                    )

                    # PASO 3: Redacción (solo si aprobado)
                    logger.info("✍️ FASE 3: Redacción")
                    writer = create_writer_agent()

                    task_write = Task(
                        description=(
                            f"Redactar artículo periodístico basándose ÚNICAMENTE en:\n\n"
                            f"INVESTIGACIÓN:\n{investigation_result}\n\n"
                            f"ANÁLISIS APROBADO:\n{analysis_result}\n\n"
                            "Seguir estructura de pirámide invertida. Usar solo hechos validados."
                        ),
                        expected_output=(
                            "Artículo completo en markdown:\n"
                            "- Título (# nivel 1)\n"
                            "- Lead en negrita\n"
                            "- Cuerpo estructurado\n"
                            "- Fuentes al final"
                        ),
                        agent=writer,
                    )

                    writing_crew = Crew(
                        agents=[writer],
                        tasks=[task_write],
                        process=Process.sequential,
                        verbose=True,
                    )

                    self.callback.on_agent_start(
                        "Redactor Senior", "Escribiendo artículo final..."
                    )
                    final_article = writing_crew.kickoff()
                    self.callback.on_agent_finish(
                        "Redactor Senior", "Artículo finalizado"
                    )

                    self.callback.on_crew_finish(final_article)
                    logger.info("🎉 Noticia generada exitosamente")

                    return {
                        "status": "success",
                        "topic": topic,
                        "article": str(final_article),
                        "iterations": iteration,
                        "session_id": self.session_id,
                    }

                elif "RECHAZADO" in analysis_text:
                    logger.warning(
                        f"❌ Analista RECHAZÓ el contenido en iteración {iteration}"
                    )
                    logger.info(f"📋 Feedback del Analista:\n{str(analysis_result)}")

                    if iteration < MAX_ITERATIONS:
                        logger.info(
                            f"🔄 BACKTRACKING: Refinando búsqueda con feedback del Analista"
                        )
                        self.callback.on_backtracking(str(analysis_result))
                        # El bucle continuará con nueva investigación
                        # Aquí podrías modificar el topic con el feedback del analista
                        feedback_text = str(analysis_result)[:200]
                        topic = f"{topic} (REFINAMIENTO: {feedback_text})"
                    else:
                        logger.error(
                            "❌ Máximo de iteraciones alcanzado sin aprobación"
                        )
                        return {
                            "status": "error",
                            "topic": topic,
                            "error": f"Contenido rechazado después de {MAX_ITERATIONS} intentos. Último feedback: {analysis_result}",
                            "session_id": self.session_id,
                        }
                else:
                    logger.error("⚠️ Analista no emitió veredicto claro")
                    logger.info(f"Respuesta ambigua: {str(analysis_result)}")
                    # Tratar como rechazo por seguridad
                    continue

            # Si llega aquí, se agotaron las iteraciones
            return {
                "status": "error",
                "topic": topic,
                "error": f"No se logró aprobación después de {MAX_ITERATIONS} iteraciones",
                "session_id": self.session_id,
            }

        except Exception as e:
            error_msg = f"Error durante ejecución de crew: {str(e)}"
            logger.error(f"❌ {error_msg}")
            self.callback.on_error(error_msg)

            return {
                "status": "error",
                "topic": topic,
                "error": error_msg,
                "session_id": self.session_id,
            }


# =============================================================================
# FUNCIÓN DE UTILIDAD PARA USAR DESDE APP.PY
# =============================================================================


def generate_news_article(
    topic: str, session_id: str = "default", current_date: str = ""
) -> Dict[str, Any]:
    """
    Función principal para generar un artículo de noticias.

    Esta es la interfaz pública que usa el servidor Flask.

    Args:
        topic: Tema sobre el que escribir
        session_id: ID de sesión para tracking
        current_date: Fecha actual (YYYY-MM-DD). Si None, usa datetime.now()

    Returns:
        Resultado de la ejecución de la crew
    """
    if current_date is None:
        from datetime import datetime

        current_date = datetime.now().strftime("%Y-%m-%d")

    logger.info(f"📅 generate_news_article llamada con fecha: {current_date}")

    crew = NewsCrew(session_id, current_date)
    return crew.run(topic, current_date)


if __name__ == "__main__":
    """
    Test standalone de la crew (sin frontend).
    """
    print("=" * 80)
    print("🧪 MODO TEST - SISTEMA MULTIAGENTE DE NOTICIAS")
    print("=" * 80)
    print("\nNOTA: Este test requiere:")
    print("  1. API_RALF corriendo y configurada en .env")
    print("  2. ScraperRalf corriendo en localhost:5000")
    print("\n" + "=" * 80 + "\n")

    # Test con tema de ejemplo
    test_topic = "Avances recientes en inteligencia artificial"

    print(f"📰 Generando artículo sobre: '{test_topic}'\n")

    result = generate_news_article(test_topic, session_id="test-cli")

    print("\n" + "=" * 80)
    print("📄 RESULTADO:")
    print("=" * 80 + "\n")

    if result.get("status") == "success":  # type: ignore
        print(result.get("article"))  # type: ignore
    else:
        print(f"❌ Error: {result.get('error')}")  # type: ignore

    print("\n" + "=" * 80)

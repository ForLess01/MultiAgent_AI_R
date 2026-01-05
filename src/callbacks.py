"""
=============================================================================
MÓDULO: Sistema de Callbacks para Visualización en Tiempo Real
=============================================================================

Implementa el puente entre el razonamiento de los agentes y la interfaz visual,
emitiendo eventos Socket.IO para mostrar el flujo de trabajo tipo n8n.

FUNDAMENTACIÓN TEÓRICA:
- Observabilidad de Sistemas Multiagente (AIMA Cap. 17.4)
- Permite "ver dentro de la mente" del agente durante la ejecución
- Crucial para debugging y confianza del usuario (Explainable AI)

ARQUITECTURA:
- Intercepta eventos de CrewAI mediante callbacks
- Emite eventos Socket.IO al frontend
- Mantiene estado del flujo de ejecución
"""

import logging
from typing import Any, Dict, Optional
from datetime import datetime
import json

# Importaciones de Socket.IO (se inyectará la instancia)
socketio_instance = None

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def set_socketio(socketio):
    """
    Inyecta la instancia de SocketIO para uso en callbacks.

    Args:
        socketio: Instancia de flask_socketio.SocketIO
    """
    global socketio_instance
    socketio_instance = socketio
    logger.info("✅ Socket.IO inyectado en el sistema de callbacks")


class RealtimeAgentCallback:
    """
    Callback handler para emitir eventos en tiempo real al frontend.

    TEORÍA (AIMA Cap. 17):
    - Implementa "Trazabilidad de Decisiones" en agentes
    - Cada acción del agente genera un evento observable
    - Permite construcción de grafo de ejecución en UI

    EVENTOS EMITIDOS:
    - crew_start: Inicio de la crew
    - agent_start: Un agente comienza su tarea
    - agent_thinking: El agente está razonando (LLM procesando)
    - tool_start: Inicio de uso de herramienta
    - tool_end: Fin de uso de herramienta
    - agent_finish: Un agente completa su tarea
    - crew_finish: Finalización de toda la crew
    - error: Cualquier error durante la ejecución
    """

    def __init__(self, session_id: str = "default"):
        """
        Inicializa el callback handler.

        Args:
            session_id: Identificador único de la sesión para múltiples usuarios
        """
        self.session_id = session_id
        self.start_time = datetime.now()
        self.current_agent = None
        self.task_counter = 0
        logger.info(f"🎬 Callback handler iniciado (session: {session_id})")

    def _emit(self, event_name: str, data: Dict[str, Any]):
        """
        Emite un evento Socket.IO al frontend.

        Args:
            event_name: Nombre del evento
            data: Payload del evento
        """
        if socketio_instance is None:
            logger.warning("⚠️ Socket.IO no configurado, evento no emitido")
            return

        # Agregar metadata común
        payload = {
            **data,
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "elapsed_time": (datetime.now() - self.start_time).total_seconds(),
        }

        # Emitir evento
        try:
            socketio_instance.emit(event_name, payload, namespace="/agents")
            logger.debug(f"📡 Emitido: {event_name} -> {data.get('agent', 'N/A')}")
        except Exception as e:
            logger.error(f"❌ Error emitiendo evento {event_name}: {e}")

    # =========================================================================
    # CALLBACKS DE CREW
    # =========================================================================

    def on_crew_start(self, crew_name: str, tasks_count: int):
        """
        Se llama cuando la crew inicia ejecución.

        Teoría (AIMA Cap. 11.3):
        - Inicio de Planificación HTN
        - Descomposición de objetivo global en subtareas
        """
        self._emit(
            "crew_start",
            {
                "crew_name": crew_name,
                "tasks_count": tasks_count,
                "message": f"🚀 Iniciando sistema {crew_name} con {tasks_count} tareas",
            },
        )

    def on_crew_finish(self, result: Any):
        """
        Se llama cuando la crew completa todas las tareas.
        """
        self._emit(
            "crew_finish",
            {
                "result": str(result)[:500],  # Truncar para no saturar
                "total_time": (datetime.now() - self.start_time).total_seconds(),
                "message": "🎉 Proceso completado exitosamente",
            },
        )

    # =========================================================================
    # CALLBACKS DE AGENTES
    # =========================================================================

    def on_agent_start(self, agent_name: str, task_description: str):
        """
        Se llama cuando un agente comienza su tarea.

        Args:
            agent_name: Nombre del agente (Investigador, Analista, etc.)
            task_description: Descripción de la tarea asignada
        """
        self.current_agent = agent_name
        self.task_counter += 1

        self._emit(
            "agent_start",
            {
                "agent": agent_name,
                "task": task_description[:200],
                "task_number": self.task_counter,
                "message": f"🤖 {agent_name} iniciando trabajo",
            },
        )

    def on_agent_thinking(self, agent_name: str, thought: str):
        """
        Se llama cuando el agente está razonando (pensando).

        Teoría (AIMA Cap. 2.4):
        - Visualización del proceso deliberativo interno
        - Crucial para entender la "cadena de razonamiento"
        """
        self._emit(
            "agent_thinking",
            {
                "agent": agent_name,
                "thought": thought[:300],
                "message": f"💭 {agent_name} está razonando...",
            },
        )

    def on_agent_finish(self, agent_name: str, output: str):
        """
        Se llama cuando un agente completa su tarea.
        """
        self._emit(
            "agent_finish",
            {
                "agent": agent_name,
                "output": output[:400],
                "message": f"✅ {agent_name} completó su tarea",
            },
        )

        self.current_agent = None

    def on_backtracking(self, feedback: str):
        """
        Se llama cuando el Analista rechaza y se activa el backtracking.

        Teoría (AIMA Cap. 12.6):
        - Visualización del bucle de retroalimentación
        - Muestra el flujo no lineal del sistema
        """
        self._emit(
            "backtracking",
            {
                "agent": "Analista de Sesgos y Fact-Checker",
                "target": "Investigador de Noticias",
                "feedback": feedback[:300],
                "message": "🔄 RECHAZADO: Volviendo a investigar...",
            },
        )

    # =========================================================================
    # CALLBACKS DE HERRAMIENTAS
    # =========================================================================

    def on_tool_start(self, tool_name: str, tool_input: Dict[str, Any]):
        """
        Se llama cuando un agente comienza a usar una herramienta.

        Teoría (AIMA Cap. 2.3):
        - Activación de sensores/efectores del agente
        - Interacción con el entorno externo
        """
        self._emit(
            "tool_start",
            {
                "agent": self.current_agent or "Unknown",
                "tool": tool_name,
                "input": str(tool_input)[:200],
                "message": f"🔧 Usando herramienta: {tool_name}",
            },
        )

    def on_tool_end(self, tool_name: str, tool_output: str):
        """
        Se llama cuando una herramienta retorna resultado.

        LOGGING MEJORADO:
        - Muestra distribución de fuentes para NewsSearchTool
        - Alerta si solo se reciben APIs globales (problema de timeout)
        """
        # Intentar parsear si es JSON
        output_preview = ""
        alert_message = None

        try:
            parsed_output = json.loads(tool_output)
            output_preview = f"Status: {parsed_output.get('status', 'N/A')}"

            if "total_results" in parsed_output:
                total = parsed_output["total_results"]
                deep = parsed_output.get("deep_sources_count", 0)
                api = parsed_output.get("api_sources_count", 0)

                output_preview += f" | Total: {total}"
                output_preview += f" | 🟢Tier1: {deep}"
                output_preview += f" | 🟡Tier2: {api}"

                # ALERTA si solo hay APIs (problema de timeout interno de ScraperRalf)
                if deep == 0 and api > 0:
                    alert_message = "⚠️ ADVERTENCIA: Solo APIs globales recibidas. Scrapers locales no respondieron."
                    logger.warning(alert_message)
                    logger.warning("   Posibles causas:")
                    logger.warning("   1. ScraperRalf tiene timeout interno < 90s")
                    logger.warning("   2. Scrapers locales están fallando")
                    logger.warning("   3. Camoufox no instalado: 'camoufox fetch'")

        except:
            output_preview = tool_output[:150]

        self._emit(
            "tool_end",
            {
                "agent": self.current_agent or "Unknown",
                "tool": tool_name,
                "output": output_preview,
                "alert": alert_message,
                "message": f"✅ {tool_name} completado",
            },
        )

    # =========================================================================
    # CALLBACKS DE ERRORES Y LOGS
    # =========================================================================

    def on_error(self, error_message: str, agent_name: Optional[str] = None):
        """
        Se llama cuando ocurre un error.

        Teoría (AIMA Cap. 12.6):
        - Manejo de Incertidumbre y Errores
        - Permite replanificación o intervención humana
        """
        self._emit(
            "error",
            {
                "agent": agent_name or self.current_agent or "System",
                "error": error_message,
                "message": f"❌ Error: {error_message[:100]}",
            },
        )

    def on_log(self, log_message: str, level: str = "info"):
        """
        Envía un mensaje de log al frontend.
        """
        self._emit(
            "log",
            {
                "agent": self.current_agent or "System",
                "message": log_message,
                "level": level,
            },
        )


class CrewCallbackHandler:
    """
    Wrapper para integrar RealtimeAgentCallback con CrewAI.

    CrewAI usa un sistema de callbacks específico. Esta clase
    adapta nuestro callback a la interfaz esperada.
    """

    def __init__(self, session_id: str = "default"):
        self.callback = RealtimeAgentCallback(session_id)

    def on_task_start(self, task):
        """Hook de CrewAI cuando inicia una tarea."""
        agent_name = task.agent.role if hasattr(task, "agent") else "Unknown"
        self.callback.on_agent_start(agent_name, task.description)

    def on_task_end(self, task, output):
        """Hook de CrewAI cuando termina una tarea."""
        agent_name = task.agent.role if hasattr(task, "agent") else "Unknown"
        self.callback.on_agent_finish(agent_name, str(output))

    def on_tool_start(self, tool, input_data):
        """Hook de CrewAI cuando usa una herramienta."""
        self.callback.on_tool_start(tool.name, input_data)

    def on_tool_end(self, tool, output):
        """Hook de CrewAI cuando termina de usar una herramienta."""
        self.callback.on_tool_end(tool.name, output)


# Singleton global para uso en crew.py
_global_callback = None


def get_callback_handler(session_id: str = "default") -> RealtimeAgentCallback:
    """
    Factory para obtener instancia de callback.

    Args:
        session_id: ID de sesión para tracking

    Returns:
        Instancia de RealtimeAgentCallback
    """
    global _global_callback
    if _global_callback is None or _global_callback.session_id != session_id:
        _global_callback = RealtimeAgentCallback(session_id)
    return _global_callback


if __name__ == "__main__":
    """
    Test de callbacks sin Socket.IO (modo simulado).
    """
    print("🧪 Probando sistema de callbacks...\n")

    callback = RealtimeAgentCallback("test-session")

    # Simular flujo de ejecución
    callback.on_crew_start("NewsCrew", 3)
    callback.on_agent_start("Investigador", "Buscar noticias sobre IA")
    callback.on_tool_start("news_search", {"query": "IA"})
    callback.on_tool_end("news_search", '{"status": "success", "total_results": 5}')
    callback.on_agent_finish("Investigador", "Encontradas 5 noticias relevantes")
    callback.on_crew_finish("Artículo generado")

    print(
        "\n✅ Test completado. En producción, estos eventos se emitirían por Socket.IO"
    )

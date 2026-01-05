"""
=============================================================================
APLICACIÓN: Servidor Flask con Socket.IO para Dashboard Multiagente
=============================================================================

Servidor web que expone el sistema multiagente mediante una interfaz visual
en tiempo real, similar a n8n, donde se puede observar el flujo de ejecución.

ARQUITECTURA:
- Flask: Servidor HTTP para endpoints REST y servir frontend
- Socket.IO: Comunicación bidireccional en tiempo real
- Threading: Ejecución de crew en background para no bloquear UI

ENDPOINTS:
- GET /              : Dashboard principal
- POST /api/generate : Inicia generación de noticia
- WS /agents         : Namespace Socket.IO para eventos en vivo
"""

import os
import uuid
from flask import Flask, render_template, request as flask_request, jsonify
from flask_socketio import SocketIO, emit, join_room
from flask_cors import CORS
from dotenv import load_dotenv
import logging
from threading import Thread
from datetime import datetime

# Importaciones locales
from src.crew import generate_news_article
from src.callbacks import set_socketio
from src.formatting import format_news_article

# Configurar logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

# =============================================================================
# CONFIGURACIÓN DE FLASK Y SOCKET.IO
# =============================================================================

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv(
    "FLASK_SECRET_KEY", "dev-secret-key-change-in-production"
)
app.config["DEBUG"] = os.getenv("FLASK_DEBUG", "True").lower() == "true"

# Habilitar CORS para desarrollo
CORS(app)

# Inicializar Socket.IO
socketio = SocketIO(
    app,
    cors_allowed_origins="*",  # En producción, especificar dominios permitidos
    async_mode="threading",
    logger=True,
    engineio_logger=False,
)

# Inyectar Socket.IO en el sistema de callbacks
set_socketio(socketio)

logger.info("✅ Flask y Socket.IO inicializados")

# =============================================================================
# ALMACENAMIENTO EN MEMORIA (Para demo - usar DB en producción)
# =============================================================================

# Diccionario para almacenar sesiones activas
active_sessions = {}

# Diccionario para almacenar resultados
results_cache = {}


# =============================================================================
# RUTAS HTTP
# =============================================================================


@app.route("/")
def index():
    """
    Página principal del dashboard.
    """
    return render_template("index.html")


@app.route("/api/health", methods=["GET"])
def health_check():
    """
    Endpoint de health check para monitoreo.
    """
    return jsonify(
        {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "active_sessions": len(active_sessions),
        }
    )


@app.route("/api/generate", methods=["POST"])
def generate_article():
    """
    Inicia la generación de un artículo de noticias.

    FLUJO:
    1. Recibe tema por POST
    2. Genera session_id único
    3. Lanza crew en thread separado (no bloquea)
    4. Retorna session_id al cliente
    5. Cliente se suscribe a eventos Socket.IO con ese session_id

    Request Body:
        {
            "topic": "Tema de la noticia"
        }

    Response:
        {
            "status": "started",
            "session_id": "uuid-xxx",
            "topic": "..."
        }
    """
    try:
        # Validar request
        data = flask_request.get_json()

        if not data or "topic" not in data:
            return (
                jsonify(
                    {"status": "error", "message": 'Campo "topic" requerido en el body'}
                ),
                400,
            )

        topic = data["topic"].strip()

        if not topic:
            return (
                jsonify({"status": "error", "message": "El tema no puede estar vacío"}),
                400,
            )

        # Generar session_id único
        session_id = str(uuid.uuid4())

        # Registrar sesión
        active_sessions[session_id] = {
            "topic": topic,
            "started_at": datetime.now().isoformat(),
            "status": "running",
        }

        logger.info(f"🚀 Nueva sesión iniciada: {session_id} | Tema: '{topic}'")

        # Lanzar generación en thread separado
        thread = Thread(target=run_crew_async, args=(topic, session_id))
        thread.daemon = True
        thread.start()

        return (
            jsonify(
                {
                    "status": "started",
                    "session_id": session_id,
                    "topic": topic,
                    "message": "Generación iniciada. Conéctate al namespace /agents con este session_id",
                }
            ),
            202,
        )  # 202 Accepted

    except Exception as e:
        logger.error(f"❌ Error en /api/generate: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/result/<session_id>", methods=["GET"])
def get_result(session_id):
    """
    Obtiene el resultado de una sesión finalizada.

    Args:
        session_id: ID de la sesión

    Response:
        {
            "status": "completed" | "running" | "error",
            "article": "...",  // Si está completado
            "error": "...",    // Si hubo error
            ...
        }
    """
    if session_id not in active_sessions:
        return jsonify({"status": "error", "message": "Sesión no encontrada"}), 404

    session_info = active_sessions[session_id]

    # Si está en cache de resultados, retornar
    if session_id in results_cache:
        return jsonify(results_cache[session_id])

    # Si aún está corriendo
    return jsonify(
        {
            "status": session_info["status"],
            "topic": session_info["topic"],
            "started_at": session_info["started_at"],
        }
    )


# =============================================================================
# EVENTOS SOCKET.IO
# =============================================================================


@socketio.on("connect", namespace="/agents")
def handle_connect():
    """
    Maneja conexión de cliente al namespace /agents.
    """
    from flask import request

    sid = request.sid if hasattr(request, "sid") else "unknown"  # type: ignore[attr-defined]
    logger.info(f"🔌 Cliente conectado: {sid}")
    emit(
        "connected",
        {"message": "Conectado al sistema multiagente", "sid": sid},
    )


@socketio.on("disconnect", namespace="/agents")
def handle_disconnect():
    """
    Maneja desconexión de cliente.
    """
    from flask import request

    sid = request.sid if hasattr(request, "sid") else "unknown"  # type: ignore[attr-defined]
    logger.info(f"🔌 Cliente desconectado: {sid}")


@socketio.on("join_session", namespace="/agents")
def handle_join_session(data):
    """
    Permite a un cliente unirse a una sesión específica.

    Args:
        data: {"session_id": "uuid-xxx"}
    """
    session_id = data.get("session_id")

    if not session_id:
        emit("error", {"message": "session_id requerido"})
        return

    if session_id not in active_sessions:
        emit("error", {"message": "Sesión no encontrada"})
        return

    # Unir cliente a room de la sesión
    join_room(session_id)

    from flask import request

    sid = request.sid if hasattr(request, "sid") else "unknown"  # type: ignore[attr-defined]
    logger.info(f"👥 Cliente {sid} se unió a sesión {session_id}")

    emit(
        "joined_session",
        {"session_id": session_id, "topic": active_sessions[session_id]["topic"]},
    )


@socketio.on("ping", namespace="/agents")
def handle_ping():
    """
    Endpoint para keepalive del cliente.
    """
    emit("pong", {"timestamp": datetime.now().isoformat()})


# =============================================================================
# FUNCIÓN AUXILIAR PARA EJECUCIÓN ASYNC
# =============================================================================


def run_crew_async(topic: str, session_id: str):
    """
    Ejecuta la crew en un thread separado y emite resultado al finalizar.

    Args:
        topic: Tema de la noticia
        session_id: ID de la sesión
    """
    try:
        logger.info(f"🎬 Iniciando crew para sesión {session_id}")

        # Obtener fecha actual
        from datetime import datetime

        current_date = datetime.now().strftime("%Y-%m-%d")
        logger.info(f"📅 Fecha de referencia del sistema: {current_date}")

        # Ejecutar crew (esto lanzará eventos Socket.IO automáticamente)
        result = generate_news_article(topic, session_id, current_date)

        # Formatear el artículo para asegurar estructura correcta
        if result.get("status") == "success" and result.get("article"):
            try:
                logger.info("🧹 Aplicando formateo de limpieza al artículo...")
                result["article"] = format_news_article(result["article"])
            except Exception as e:
                logger.warning(f"⚠️ Error al formatear artículo: {e}")
                # Continuamos con el artículo original si falla el formateo

        # Actualizar estado de sesión
        active_sessions[session_id]["status"] = result["status"]
        active_sessions[session_id]["finished_at"] = datetime.now().isoformat()

        # Guardar en cache
        results_cache[session_id] = result

        # Emitir evento final
        socketio.emit("generation_complete", result, namespace="/agents", to=session_id)

        logger.info(f"✅ Sesión {session_id} completada: {result['status']}")

    except Exception as e:
        error_msg = f"Error en crew async: {str(e)}"
        logger.error(f"❌ {error_msg}")

        # Emitir error
        socketio.emit(
            "generation_error",
            {"session_id": session_id, "error": error_msg},
            namespace="/agents",
            to=session_id,
        )

        # Actualizar sesión
        active_sessions[session_id]["status"] = "error"
        active_sessions[session_id]["error"] = error_msg


# =============================================================================
# PUNTO DE ENTRADA
# =============================================================================

if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", 8080))
    debug = os.getenv("FLASK_DEBUG", "True").lower() == "true"

    print("=" * 80)
    print("🚀 SISTEMA MULTIAGENTE DE PRODUCCIÓN DE NOTICIAS")
    print("=" * 80)
    print(f"\n📍 Dashboard disponible en: http://localhost:{port}")
    print(f"🔌 Socket.IO namespace: /agents")
    print(f"🐛 Modo Debug: {debug}")
    print("\n" + "=" * 80 + "\n")
    print("⚠️  REQUERIMIENTOS ANTES DE USAR:")
    print("  1. API_RALF debe estar corriendo (ver .env)")
    print("  2. ScraperRalf debe estar en http://localhost:5000")
    print("\n" + "=" * 80 + "\n")

    # Iniciar servidor
    socketio.run(
        app,
        host="0.0.0.0",
        port=port,
        debug=debug,
        allow_unsafe_werkzeug=True,  # Solo para desarrollo
    )

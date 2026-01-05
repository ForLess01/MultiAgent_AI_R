"""
Proxy que convierte el formato OpenAI al formato de API_RALF.
Este servidor se ejecuta localmente y traduce las peticiones.
"""

from flask import Flask, request, Response, stream_with_context
import requests
import json
import os
import time
import random
from dotenv import load_dotenv
from typing import Dict, Any, Tuple, Optional
import logging

load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

RALF_ENDPOINT = os.getenv(
    "RALF_ENDPOINT", "http://ygggo88wk0wo8ogckoscgw0o.72.62.170.143.sslip.io/chat"
)

# Configuración de reintentos para rate limits
MAX_RETRIES = int(os.getenv("RALF_MAX_RETRIES", "5"))
BASE_DELAY = float(os.getenv("RALF_BASE_DELAY", "2.0"))  # segundos
MAX_DELAY = float(os.getenv("RALF_MAX_DELAY", "60.0"))  # segundos
JITTER_RANGE = float(os.getenv("RALF_JITTER_RANGE", "0.5"))  # +/- 50%


def call_ralf_with_retry(
    ralf_payload: Dict[str, Any], stream: bool = False, timeout: int = 60
) -> Tuple[Optional[requests.Response], Optional[Dict[str, Any]]]:
    """
    Llama a la API RALF con lógica de reintentos exponencial.
    Retorna (response, error). Si hay error, response es None.
    """
    last_error = None

    for attempt in range(MAX_RETRIES):
        try:
            if attempt > 0:
                logger.info(f"🔄 Reintento {attempt + 1}/{MAX_RETRIES} para RALF...")

            response = requests.post(
                RALF_ENDPOINT, json=ralf_payload, stream=stream, timeout=timeout
            )

            # Si es exitoso (200-299), retornar respuesta
            if 200 <= response.status_code < 300:
                return response, None

            # Si es error de cliente (4xx) que no sea 429, no reintentar
            if 400 <= response.status_code < 500 and response.status_code != 429:
                error_msg = (
                    f"Error cliente RALF: {response.status_code} - {response.text}"
                )
                logger.error(error_msg)
                return None, {"error": error_msg, "status_code": response.status_code}

            # Si es 429 o 5xx, reintentar
            error_msg = (
                f"Error temporal RALF: {response.status_code} - {response.text[:200]}"
            )
            logger.warning(error_msg)
            last_error = {"error": error_msg, "status_code": response.status_code}

        except requests.RequestException as e:
            error_msg = f"Excepción conexión RALF: {str(e)}"
            logger.warning(error_msg)
            last_error = {"error": error_msg, "status_code": 503}

        # Calcular espera con backoff exponencial y jitter
        # delay = base * (2 ^ attempt) + jitter
        delay = min(MAX_DELAY, BASE_DELAY * (2**attempt))
        jitter = delay * JITTER_RANGE * (random.random() * 2 - 1)  # +/- range
        final_delay = max(0.5, delay + jitter)

        if attempt < MAX_RETRIES - 1:
            logger.info(
                f"⏳ Esperando {final_delay:.2f}s antes del siguiente reintento..."
            )
            time.sleep(final_delay)

    return None, last_error


@app.route("/v1/chat/completions", methods=["POST"])
def chat_completions():
    """Convierte formato OpenAI a formato API_RALF"""

    try:
        # Obtener datos en formato OpenAI
        openai_data = request.get_json()

        if not openai_data:
            return {"error": "No JSON data provided"}, 400

        print(f"📥 Petición recibida: {json.dumps(openai_data, indent=2)}")

        # Extraer mensajes
        messages = openai_data.get("messages", [])

        if not messages:
            return {"error": "No messages provided"}, 400

        # Convertir al formato de API_RALF
        ralf_payload = {"messages": messages}

        print(f"📤 Enviando a RALF: {json.dumps(ralf_payload, indent=2)}")

        # Llamar a API_RALF con manejo de rate limits
        is_streaming = openai_data.get("stream", False)
        response, error = call_ralf_with_retry(
            ralf_payload=ralf_payload, stream=is_streaming, timeout=60
        )

        # Si hubo error, retornarlo
        if error is not None:
            status_code = error.get("status_code", 500)
            error_message = error.get("error", "Unknown error")

            # Agregar sugerencias al usuario
            if status_code == 429 or "rate limit" in error_message.lower():
                error_message += (
                    " | Sugerencia: La API_RALF está sobrecargada. "
                    "Espera unos minutos antes de reintentar."
                )

            print(f"❌ Error final de RALF: {error_message}")
            return {"error": error_message}, status_code

        if response is None:
            return {"error": "No response received from RALF service"}, 500

        print(f"📡 Respuesta RALF exitosa: status 200")

        # Si es streaming, reenviar como OpenAI streaming
        if is_streaming:

            def generate():
                for line in response.iter_lines():
                    if line:
                        # Formato OpenAI streaming
                        chunk = {
                            "choices": [
                                {
                                    "delta": {"content": line.decode("utf-8")},
                                    "index": 0,
                                    "finish_reason": None,
                                }
                            ]
                        }
                        yield f"data: {json.dumps(chunk)}\n\n"

                # Final del stream
                yield "data: [DONE]\n\n"

            return Response(
                stream_with_context(generate()), mimetype="text/event-stream"
            )

        # Si no es streaming, devolver respuesta completa
        full_response = ""
        for line in response.iter_lines():
            if line:
                full_response += line.decode("utf-8")

        # Formato OpenAI no-streaming
        openai_response = {
            "id": "chatcmpl-proxy",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "ralf-mixed-model",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": full_response},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        }

        return openai_response

    except Exception as e:
        error_msg = f"Error interno del proxy: {str(e)}"
        logger.error(f"❌ {error_msg}")
        import traceback

        traceback.print_exc()
        return {"error": error_msg}, 500


if __name__ == "__main__":
    print("🔄 RALF Proxy iniciado en http://localhost:11434")
    print(f"📡 Reenviando a: {RALF_ENDPOINT}")
    app.run(host="127.0.0.1", port=11434, debug=False)

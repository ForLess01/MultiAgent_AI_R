# Sistema Multiagente de Producción de Noticias

Sistema avanzado de generación de contenido periodístico usando **CrewAI** y **Planificación HTN** (Hierarchical Task Network), con visualización en tiempo real tipo n8n.

## 🎯 Características Principales

- **Arquitectura Multiagente Cooperativa**: 4 agentes especializados trabajando en conjunto
- **Planificación HTN**: Basado en Russell & Norvig (AIMA Cap. 11.3)
- **Monitoreo de Sesgos**: Verificación activa de calidad y neutralidad
- **Visualización en Tiempo Real**: Dashboard tipo n8n con Socket.IO
- **APIs Propias**: 100% independiente de servicios externos
- **✨ NUEVO: Grounding Temporal** - Filtrado automático de fuentes obsoletas
- **✨ NUEVO: Triangulación de Fuentes** - Búsqueda estructurada (oficial + internacional + local)
- **✨ NUEVO: Sanity Check Matemático** - Validación de coherencia lógica antes de publicar

## 📂 Estructura del Proyecto

```
MultiAgent_AI_R/
├── .env                # Configuración APIs
├── app.py             # Servidor Flask + Socket.IO
├── src/
│   ├── llm_config.py  # LLM personalizado
│   ├── tools.py       # ScraperRalf integration
│   ├── callbacks.py   # Eventos tiempo real
│   └── crew.py        # Sistema HTN
└── templates/
    └── index.html     # Dashboard visual
```

---

# 🚀 GUÍA RÁPIDA DE USO

## Pre-requisitos

### 1. APIs Propias Funcionando

**API_RALF (LLM):**
- Debe estar accesible en la URL configurada en `.env`
- Compatible con API de OpenAI
- Endpoint: `/v1/chat/completions`

**ScraperRalf (Búsqueda):**
- Debe estar corriendo en `http://localhost:5000`
- Endpoint: `GET /api/search?q={query}&max_results={n}`
- Respuesta: `{"results": [{"title": "", "content": "", "source": ""}]}`

### 2. Python 3.9+

```bash
python --version  # Debe ser >= 3.9
```

## Instalación en 3 Pasos

### Paso 1: Instalar Dependencias

```bash
pip install -r requirements.txt
```

### Paso 2: Configurar .env

Editar el archivo `.env` y actualizar:

```bash
DOMINIO_API_RALF=tu-dominio-real.com
RALF_API_KEY=tu-api-key-si-aplica
```

### Paso 3: Verificar Setup

```bash
python setup_check.py
```

Si todo está ✓, continuar. Si hay errores ✗, corregir.

## Ejecución

### Modo Completo (con Dashboard)

```bash
python app.py
```

Luego abrir en navegador: **http://localhost:8080**

### Modo CLI (solo backend, sin UI)

```bash
python src/crew.py
```

## Uso del Dashboard

1. **Ingresar tema** en el campo de texto
   - Ejemplo: "Inteligencia artificial en medicina"

2. **Clic en "Generar Noticia"**

3. **Observar el flujo en vivo:**
   - Nodos se iluminan cuando el agente está activo
   - Panel de logs muestra razonamiento en tiempo real
   - Conexiones muestran flujo de datos

4. **Leer el artículo generado**
   - Aparece al final del proceso
   - Formato profesional estilo periodístico

## Flujo del Proceso

```
1. Jefe de Redacción recibe tema
   ↓
2. Asigna tarea a Investigador
   ↓
3. Investigador busca información (ScraperRalf)
   ↓
4. Analista de Sesgos verifica calidad
   ↓
   ├─ SI detecta problemas → Volver a paso 3
   └─ SI aprueba → Continuar
   ↓
5. Redactor escribe artículo
   ↓
6. Jefe revisa y publica
```

## Troubleshooting

### "No se puede conectar con API_RALF"

1. Verificar que el servicio esté corriendo
2. Probar con curl:
   ```bash
   curl https://tu-dominio.com/v1/chat/completions
   ```
3. Revisar firewall/certificados SSL

### "ScraperRalf no disponible"

1. Iniciar el servicio ScraperRalf
2. Verificar que escucha en puerto 5000:
   ```bash
   curl http://localhost:5000/api/search?q=test
   ```

### "Socket.IO no conecta"

1. Revisar consola del navegador (F12)
2. Verificar que Flask esté en `0.0.0.0:8080`
3. Deshabilitar temporalmente firewall/antivirus

### "Módulo no encontrado"

```bash
pip install -r requirements.txt --upgrade
```

## Personalización

### Cambiar temperatura de agentes

Editar [src/crew.py](src/crew.py):

```python
def get_investigator_llm():
    return config.get_llm(temperature=0.3)  # ← Cambiar aquí
```

### Agregar nuevas herramientas

1. Crear clase en [src/tools.py](src/tools.py)
2. Heredar de `BaseTool`
3. Implementar método `_run()`
4. Asignar a agente en [src/crew.py](src/crew.py)

### Modificar personalidad de agentes

Editar `backstory` en [src/crew.py](src/crew.py), función `create_*_agent()`

## API REST Endpoints

### POST /api/generate

Inicia generación de noticia.

**Request:**
```json
{
  "topic": "Tu tema aquí"
}
```

**Response:**
```json
{
  "status": "started",
  "session_id": "uuid-123",
  "topic": "Tu tema"
}
```

### GET /api/result/{session_id}

Obtiene resultado de sesión.

**Response:**
```json
{
  "status": "success",
  "article": "Artículo completo...",
  "session_id": "uuid-123"
}
```

### GET /api/health

Health check del sistema.

## Socket.IO Events

Namespace: `/agents`

**Eventos emitidos por el servidor:**

- `crew_start` - Inicio del proceso
- `agent_start` - Un agente comienza
- `agent_thinking` - Razonamiento del agente
- `tool_start` - Uso de herramienta
- `tool_end` - Fin de herramienta
- `agent_finish` - Agente completa tarea
- `crew_finish` - Proceso terminado
- `generation_complete` - Artículo listo
- `error` - Error en el proceso

**Eventos enviados por el cliente:**

- `join_session` - Unirse a sesión: `{session_id: "..."}`

---

# 📐 ARQUITECTURA DEL SISTEMA

## Vista General

```
┌─────────────────────────────────────────────────────────────────┐
│                    SISTEMA MULTIAGENTE DE NOTICIAS              │
│                   (Planificación HTN - Russell & Norvig)        │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
   ┌────────┐          ┌──────────┐         ┌──────────┐
   │ Flask  │          │ CrewAI   │         │ Socket.IO│
   │ Server │◄────────►│ Agents   │◄────────│ Events   │
   └────────┘          └──────────┘         └──────────┘
        │                     │                     │
        │                     │                     │
        ▼                     ▼                     ▼
   ┌─────────┐         ┌──────────┐         ┌──────────┐
   │Dashboard│         │   HTN    │         │ Frontend │
   │   UI    │         │ Planning │         │ Real-time│
   └─────────┘         └──────────┘         └──────────┘
```

## Capas del Sistema

### 1. Capa de Presentación (Frontend)

```
┌───────────────────────────────────────────────────────┐
│                  templates/index.html                 │
│ ┌─────────────────────────────────────────────────┐   │
│ │  Dashboard Visual (estilo n8n)                  │   │
│ │  • Canvas de agentes (nodos animados)           │   │
│ │  • Panel de logs en tiempo real                 │   │
│ │  • Visualización de conexiones                  │   │
│ └─────────────────────────────────────────────────┘   │
│                                                       │
│  Tecnologías:                                         │
│  - HTML5 + CSS3 (Grid, Flexbox, Animations)          │
│  - JavaScript (Socket.IO Client)                      │
│  - SVG para conexiones dinámicas                      │
└───────────────────────────────────────────────────────┘
```

### 2. Capa de Aplicación (Backend)

```
┌───────────────────────────────────────────────────────┐
│                       app.py                          │
│ ┌─────────────────────────────────────────────────┐   │
│ │  Servidor Flask + Socket.IO                     │   │
│ │  • Endpoints REST (/api/generate, /api/result)  │   │
│ │  • Namespace Socket.IO (/agents)                │   │
│ │  • Threading para ejecución async               │   │
│ └─────────────────────────────────────────────────┘   │
│                                                       │
│  Puertos:                                             │
│  - HTTP: 8080 (configurable)                          │
│  - WebSocket: Mismo puerto                            │
└───────────────────────────────────────────────────────┘
```

### 3. Capa de Lógica de Negocio (Agentes)

```
┌───────────────────────────────────────────────────────┐
│                    src/crew.py                        │
│                                                       │
│  ┌─────────────────────────────────────────┐          │
│  │   Jefe de Redacción (Manager)           │          │
│  │   • Coordina proceso HTN                │          │
│  │   • Temperature: 0.6                    │          │
│  └──────────────┬──────────────────────────┘          │
│                 │ delega tareas                       │
│                 ▼                                     │
│  ┌─────────────────────────────────────────┐          │
│  │   Investigador (Watchdog)               │          │
│  │   • Busca información                   │          │
│  │   • Herramienta: NewsSearchTool         │          │
│  │   • Temperature: 0.3 (precisión)        │          │
│  └──────────────┬──────────────────────────┘          │
│                 │ pasa datos a                        │
│                 ▼                                     │
│  ┌─────────────────────────────────────────┐          │
│  │   Analista de Sesgos (Critic)           │          │
│  │   • Verifica calidad                    │          │
│  │   • Detecta falacias/sesgos             │          │
│  │   • Temperature: 0.5 (balance)          │          │
│  └──────────────┬──────────────────────────┘          │
│                 │ aprueba/rechaza                     │
│                 ▼                                     │
│  ┌─────────────────────────────────────────┐          │
│  │   Redactor (Writer)                     │          │
│  │   • Escribe artículo final              │          │
│  │   • Estructura: Pirámide invertida      │          │
│  │   • Temperature: 0.8 (creatividad)      │          │
│  └─────────────────────────────────────────┘          │
└───────────────────────────────────────────────────────┘
```

### 4. Capa de Integración (Herramientas y LLM)

```
┌───────────────────────────────────────────────────────┐
│              src/tools.py + src/llm_config.py         │
│                                                       │
│  ┌─────────────────────┐    ┌──────────────────────┐ │
│  │  NewsSearchTool     │    │  CustomLLM           │ │
│  │  ↓                  │    │  ↓                   │ │
│  │  ScraperRalf API    │    │  API_RALF            │ │
│  │  localhost:5000     │    │  (dominio en .env)   │ │
│  └─────────────────────┘    └──────────────────────┘ │
│                                                       │
│  Protocolo HTTP         Protocolo OpenAI-compatible  │
└───────────────────────────────────────────────────────┘
```

### 5. Capa de Observabilidad (Callbacks)

```
┌───────────────────────────────────────────────────────┐
│                  src/callbacks.py                     │
│                                                       │
│  ┌─────────────────────────────────────────┐          │
│  │  RealtimeAgentCallback                  │          │
│  │                                         │          │
│  │  Intercepta:                            │          │
│  │  • on_agent_start  → emit Socket.IO     │          │
│  │  • on_tool_start   → emit Socket.IO     │          │
│  │  • on_agent_finish → emit Socket.IO     │          │
│  │  • on_error        → emit Socket.IO     │          │
│  └─────────────────────────────────────────┘          │
│                                                       │
│  Eventos enviados al frontend en vivo                 │
└───────────────────────────────────────────────────────┘
```

## Flujo de Datos (HTN)

```
1. Usuario ingresa tema en Frontend
   │
   ▼
2. POST /api/generate → Flask Server
   │
   ├── Genera session_id
   ├── Crea thread async
   └── Retorna session_id al cliente
   │
   ▼
3. Cliente se une a namespace /agents con session_id
   │
   ▼
4. Thread ejecuta NewsCrew.run(topic)
   │
   ├── Manager descompone tarea (HTN)
   │   │
   │   ├── Task 1: Investigación
   │   │   ├── Investigador activa NewsSearchTool
   │   │   ├── NewsSearchTool → ScraperRalf API
   │   │   └── Retorna datos crudos
   │   │
   │   ├── Task 2: Análisis de Sesgos
   │   │   ├── Analista recibe output de Task 1
   │   │   ├── Ejecuta verificaciones
   │   │   └── Aprueba o solicita re-búsqueda
   │   │       │
   │   │       └── SI rechaza → LOOP a Task 1
   │   │
   │   └── Task 3: Redacción
   │       ├── Redactor recibe output de Task 2
   │       ├── Genera artículo (LLM con temp alta)
   │       └── Retorna texto final
   │
   ▼
5. Callbacks emiten eventos Socket.IO por cada paso
   │
   ▼
6. Frontend actualiza UI en tiempo real
   │
   ├── Nodos se iluminan
   ├── Logs se agregan
   └── Conexiones se animan
   │
   ▼
7. Al finalizar: emit 'generation_complete'
   │
   ▼
8. Frontend muestra artículo final
```

## Comunicación entre Componentes

```
┌─────────┐  HTTP POST    ┌──────────┐  Kickoff   ┌────────┐
│Frontend │──────────────►│  Flask   │───────────►│ Crew   │
│         │               │  Server  │            │ Agents │
│         │               └──────────┘            └────────┘
│         │                    │                       │
│         │                    │ Socket.IO Events      │
│         │◄───────────────────┼───────────────────────┘
│         │                    │                       
└─────────┘               ┌────▼─────┐           
                          │Callbacks │           
                          └──────────┘           
                          
Leyenda:
──► Flujo de control
..► Flujo de datos
◄─► Comunicación bidireccional
```

## Teoría Aplicada (AIMA)

### Planificación HTN (Cap. 11.3)

```
TAREA COMPUESTA: ProducirNoticia(tema)
├── MÉTODO: Proceso_Estándar
│   ├── PRIMITIVA: Buscar(tema)           [Investigador]
│   ├── PRIMITIVA: Validar(info)          [Analista]
│   └── PRIMITIVA: Redactar(info_válida)  [Redactor]
│
└── MÉTODO: Proceso_Con_Corrección (si Validar falla)
    ├── PRIMITIVA: Buscar(tema)
    ├── PRIMITIVA: Validar(info)
    ├── SI rechazado:
    │   └── RECURSIÓN: Buscar(tema_refinado)
    └── PRIMITIVA: Redactar(info_válida)
```

### Vigilancia de Ejecución (Cap. 12.5)

```
┌─────────────────────────────────────┐
│  Analista (Monitor de Ejecución)   │
│                                     │
│  PRECONDICIONES verificadas:        │
│  1. ≥ 2 fuentes independientes      │
│  2. Ausencia de falacias lógicas    │
│  3. Lenguaje neutral                │
│  4. Datos verificables              │
│                                     │
│  SI precondición falla:             │
│  → Trigger replanificación          │
│  → Backtracking a búsqueda          │
└─────────────────────────────────────┘
```

## Tecnologías Clave

| Componente | Tecnología | Propósito |
|------------|-----------|-----------|
| Backend | Flask 3.0 | Servidor web |
| Real-time | Socket.IO | Comunicación bidireccional |
| Agentes | CrewAI 0.28 | Framework multiagente |
| LLM | LangChain + Custom | Integración con API_RALF |
| Herramientas | BaseTool | Extensión de capacidades |
| Frontend | HTML5/CSS3/JS | Interfaz visual |
| Callback | Custom Handler | Observabilidad |

## Seguridad y Configuración

```
.env (NO commitear - contiene secrets)
├── DOMINIO_API_RALF=<URL del LLM>
├── RALF_API_KEY=<API Key si aplica>
├── SCRAPER_BASE_URL=http://localhost:5000
└── FLASK_SECRET_KEY=<Secreto para sesiones>

.gitignore
├── .env
├── __pycache__/
└── *.log
```

---

# 📡 ARQUITECTURA DE INTEGRACIÓN DE APIS

## 🔄 Flujo Completo del Sistema

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          FRONTEND (index.html)                              │
│  Usuario ingresa tema → POST /api/generate → Socket.IO listening           │
└──────────────────────────┬──────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        BACKEND (app.py - Flask)                             │
│  Thread asíncrono ejecuta → generate_news_article(topic, session_id)       │
└──────────────────────────┬──────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                   ORQUESTADOR (src/crew.py - NewsCrew)                      │
│  Bucle HTN con backtracking:                                                │
│    Iteración 1,2,3:                                                         │
│      ├─ FASE 1: Investigador                                                │
│      ├─ FASE 2: Analista (verifica calidad)                                 │
│      └─ FASE 3: Redactor (solo si APROBADO)                                 │
└──────────────────────────┬──────────────────────────────────────────────────┘
                           │
            ┌──────────────┴──────────────┐
            │                             │
            ▼                             ▼
┌───────────────────────┐      ┌────────────────────────┐
│  HERRAMIENTA          │      │  CEREBRO (LLM)         │
│  ScraperRalf          │      │  API_RALF              │
│  (tools.py)           │      │  (llm_config.py)       │
└───────────────────────┘      └────────────────────────┘
            │                             │
            │                             │
            ▼                             ▼
┌───────────────────────┐      ┌────────────────────────┐
│  API SCRAPER          │      │  PROXY LOCAL           │
│  127.0.0.1:5000       │      │  127.0.0.1:11434       │
│  /api/search          │      │  /v1/chat/completions  │
└───────────────────────┘      └────────────────────────┘
            │                             │
            │                             │
            ▼                             ▼
┌───────────────────────┐      ┌────────────────────────┐
│  NOTICIAS REALES      │      │  API_RALF REAL         │
│  (Peru: RPP, El       │      │  ygggo88wk0...sslip.io │
│   Comercio, etc.)     │      │  /chat                 │
└───────────────────────┘      └────────────────────────┘
```

---

## 🛠️ DETALLE POR COMPONENTE

### 1️⃣ **API_RALF (LLM Brain)**

#### Flujo de Ejecución:

```python
# PASO 1: Agente necesita razonar
agent.execute_task("Buscar noticias sobre IA")

# PASO 2: llm_config.py crea ChatOpenAI
llm = ChatOpenAI(
    base_url="http://127.0.0.1:11434/v1",  # ← PROXY LOCAL
    model="ralf-mixed-model",
    temperature=0.3
)

# PASO 3: Agent envía prompt al LLM
response = llm.invoke("¿Qué buscar sobre IA?")
```

#### Traducción en Proxy (ralf_proxy.py):

```python
# ENTRADA (Formato OpenAI):
{
  "model": "ralf-mixed-model",
  "messages": [
    {"role": "system", "content": "Eres un investigador experto..."},
    {"role": "user", "content": "Busca noticias sobre IA"}
  ],
  "temperature": 0.3
}

# ↓ CONVERSIÓN ↓

# SALIDA (Formato API_RALF):
{
  "messages": [
    {"role": "system", "content": "Eres un investigador experto..."},
    {"role": "user", "content": "Busca noticias sobre IA"}
  ]
}

# ↓ HTTP POST ↓
# http://ygggo88wk0wo8ogckoscgw0o.72.62.170.143.sslip.io/chat

# ↓ RESPUESTA API_RALF (Streaming) ↓
"Voy a buscar noticias sobre avances en IA en medicina y robótica..."

# ↓ CONVERSIÓN DE VUELTA ↓

# RESPUESTA (Formato OpenAI):
{
  "id": "chatcmpl-proxy",
  "object": "chat.completion",
  "model": "ralf-mixed-model",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "Voy a buscar noticias sobre avances en IA..."
    },
    "finish_reason": "stop"
  }]
}
```

**🔑 Clave:** El proxy actúa como "traductor simultáneo" entre el formato que espera LangChain (OpenAI) y el que usa tu API_RALF.

---

### 2️⃣ **ScraperRalf (News Search)**

#### Flujo de Ejecución:

```python
# PASO 1: Investigator Agent usa herramienta
tool = NewsSearchTool()
result = tool._run(
    query="inteligencia artificial medicina",
    max_results=5
)

# PASO 2: tools.py hace HTTP GET
endpoint = "http://127.0.0.1:5000/api/search"
params = {
    "q": "inteligencia artificial medicina",
    "max_results": 5
}

response = requests.get(endpoint, params=params, timeout=30)
```

#### Formato de Respuesta de ScraperRalf:

```json
{
  "status": "success",
  "query": "inteligencia artificial medicina",
  "total_results": 5,
  "results": [
    {
      "id": 1,
      "title": "IA revoluciona diagnósticos médicos en Perú",
      "content": "Hospitales peruanos implementan algoritmos...",
      "source": "RPP Noticias",
      "url": "https://rpp.pe/tecnologia/..."
    },
    {
      "id": 2,
      "title": "Robots quirúrgicos con IA llegan a Lima",
      "content": "El Hospital Rebagliati incorporó...",
      "source": "El Comercio",
      "url": "https://elcomercio.pe/salud/..."
    }
    // ... 3 más
  ]
}
```

**🔑 Clave:** ScraperRalf agrega noticias de múltiples fuentes peruanas (RPP, El Comercio, Gestión, etc.) y devuelve JSON limpio y estructurado.

---

## 📤 FORMATO DE RESPUESTA FINAL

### Flujo de Generación del Artículo:

```python
# 1. Investigator recopila información (JSON de ScraperRalf)
investigation_result = """
FUENTES CONSULTADAS:
- RPP: IA en medicina (credibilidad: alta)
- El Comercio: Robots quirúrgicos (credibilidad: alta)
...
"""

# 2. Analyst valida y aprueba
analysis_result = """
VEREDICTO: APROBADO
HECHOS VALIDADOS:
- Hospital Rebagliati implementó robot quirúrgico
- Sistema de IA diagnostica con 95% de precisión
...
"""

# 3. Writer genera artículo en MARKDOWN
final_article = """
# IA Revoluciona la Medicina en Perú

**Lima, 4 de enero de 2026** - Los hospitales peruanos están...

## Robótica Quirúrgica Avanza

El Hospital Rebagliati incorporó un sistema de cirugía asistida...

## Diagnósticos Más Precisos

Estudios demuestran que los algoritmos de IA logran una precisión...

### Fuentes
- RPP Noticias: https://rpp.pe/...
- El Comercio: https://elcomercio.pe/...
"""
```

### Entrega al Frontend:

```javascript
// Backend devuelve JSON:
{
  "status": "success",
  "topic": "IA en medicina Perú",
  "article": "# IA Revoluciona...\n\n**Lima**...",  // ← MARKDOWN CRUDO
  "iterations": 1,
  "session_id": "abc123"
}

// Frontend recibe y DEBE convertir Markdown → HTML
```

---

# 📊 FLUJO DE DATOS DETALLADO - SISTEMA MULTIAGENTE

## 🎯 Caso de Uso Completo: "Avances en IA en Medicina Peruana"

---

### 📥 FASE 1: INICIO DE SESIÓN

```
USUARIO (Frontend)
│
├─ Ingresa: "Avances en IA en medicina peruana"
├─ Click: "Deploy Agents"
│
▼
POST http://localhost:8080/api/generate
Body: {"topic": "Avances en IA en medicina peruana"}
│
▼
RESPUESTA:
{
  "status": "started",
  "session_id": "abc-123-xyz",
  "topic": "Avances en IA en medicina peruana"
}
│
▼
Socket.IO: join_session({"session_id": "abc-123-xyz"})
```

---

### 🔄 FASE 2: ITERACIÓN 1 - INVESTIGACIÓN

```
BACKEND (app.py → crew.py)
│
├─ NewsCrew.run(topic="Avances en IA en medicina peruana")
│
▼
┌────────────────────────────────────────────────────────┐
│ AGENTE: INVESTIGADOR                                   │
└────────────────────────────────────────────────────────┘
│
├─ Socket.IO emit: agent_start
│  {
│    "agent": "Investigador de Noticias",
│    "message": "🤖 Investigador activando sensores..."
│  }
│
├─ LLM (API_RALF) decide estrategia de búsqueda
│  ┌─────────────────────────────────────────────┐
│  │ PASO 1: ChatOpenAI.invoke()                 │
│  │ Prompt: "Eres investigador experto. Busca   │
│  │         información sobre: {topic}"         │
│  │                                              │
│  │ ↓ llm_config.py                             │
│  │                                              │
│  │ POST http://127.0.0.1:11434/v1/chat/...     │
│  │ Body (OpenAI format):                       │
│  │ {                                            │
│  │   "model": "ralf-mixed-model",              │
│  │   "messages": [{                             │
│  │     "role": "system",                        │
│  │     "content": "Eres investigador..."       │
│  │   }],                                        │
│  │   "temperature": 0.3                         │
│  │ }                                            │
│  │                                              │
│  │ ↓ ralf_proxy.py CONVIERTE                   │
│  │                                              │
│  │ POST http://ygggo88...sslip.io/chat         │
│  │ Body (RALF format):                         │
│  │ {                                            │
│  │   "messages": [{                             │
│  │     "role": "system",                        │
│  │     "content": "Eres investigador..."       │
│  │   }]                                         │
│  │ }                                            │
│  │                                              │
│  │ ↓ API_RALF RESPONDE (streaming)             │
│  │                                              │
│  │ "Voy a buscar usando términos específicos:  │
│  │  'inteligencia artificial hospital perú',   │
│  │  'IA diagnóstico médico Lima', etc."        │
│  │                                              │
│  │ ↓ PROXY CONVIERTE DE VUELTA                 │
│  │                                              │
│  │ Response (OpenAI format):                   │
│  │ {                                            │
│  │   "choices": [{                              │
│  │     "message": {                             │
│  │       "content": "Voy a buscar usando..."   │
│  │     }                                        │
│  │   }]                                         │
│  │ }                                            │
│  └─────────────────────────────────────────────┘
│
├─ LLM decide: "Usar herramienta news_search"
│
├─ Socket.IO emit: tool_start
│  {
│    "agent": "Investigador de Noticias",
│    "tool": "news_search",
│    "message": "🔧 Usando herramienta: news_search"
│  }
│
├─ NewsSearchTool._run()
│  ┌─────────────────────────────────────────────┐
│  │ PASO 2: ScraperRalf Query                   │
│  │                                              │
│  │ GET http://127.0.0.1:5000/api/search        │
│  │ Params:                                      │
│  │   ?q=inteligencia artificial hospital perú  │
│  │   &max_results=5                             │
│  │                                              │
│  │ ↓ ScraperRalf BUSCA EN FUENTES REALES       │
│  │                                              │
│  │ [RPP.pe] Scraped: "IA en Hospital..."       │
│  │ [ElComercio.pe] Scraped: "Robots médicos.." │
│  │ [Gestion.pe] Scraped: "Telemedicina IA..."  │
│  │                                              │
│  │ ↓ RESPUESTA JSON                             │
│  │                                              │
│  │ {                                            │
│  │   "status": "success",                       │
│  │   "total_results": 5,                        │
│  │   "results": [                               │
│  │     {                                        │
│  │       "id": 1,                               │
│  │       "title": "IA revoluciona diagnóstico..",│
│  │       "content": "Hospital Rebagliati...",  │
│  │       "source": "RPP Noticias",             │
│  │       "url": "https://rpp.pe/..."           │
│  │     },                                       │
│  │     {                                        │
│  │       "id": 2,                               │
│  │       "title": "Robots quirúrgicos IA...",  │
│  │       "content": "Clínica San Felipe...",   │
│  │       "source": "El Comercio",              │
│  │       "url": "https://elcomercio.pe/..."    │
│  │     }                                        │
│  │     // ... 3 más                             │
│  │   ]                                          │
│  │ }                                            │
│  └─────────────────────────────────────────────┘
│
├─ Socket.IO emit: tool_end
│  {
│    "tool": "news_search",
│    "message": "✅ Encontrados 5 artículos"
│  }
│
├─ LLM procesa resultados y genera informe
│  (API_RALF nuevamente, mismo flujo de proxy)
│
│  INFORME GENERADO:
│  """
│  FUENTES CONSULTADAS:
│  
│  1. RPP Noticias (Credibilidad: Alta)
│     - Título: "IA revoluciona diagnósticos en Perú"
│     - Hechos: Hospital Rebagliati implementó sistema...
│     - URL: https://rpp.pe/tecnologia/...
│  
│  2. El Comercio (Credibilidad: Alta)
│     - Título: "Robots quirúrgicos con IA en Lima"
│     - Hechos: Clínica San Felipe adquirió robot...
│     - URL: https://elcomercio.pe/salud/...
│  
│  DATOS CLAVE:
│  - 3 hospitales peruanos usan IA para diagnóstico
│  - Precisión del 95% en detección de cáncer
│  - Reducción de 40% en tiempo de diagnóstico
│  """
│
▼
Socket.IO emit: agent_finish
{
  "agent": "Investigador de Noticias",
  "message": "✅ Investigación completada"
}
```

---

### 🔍 FASE 3: ANÁLISIS DE SESGOS

```
┌────────────────────────────────────────────────────────┐
│ AGENTE: ANALISTA                                       │
└────────────────────────────────────────────────────────┘
│
├─ Socket.IO emit: agent_start
│  {"agent": "Analista de Sesgos y Fact-Checker"}
│
├─ Recibe informe del Investigador
│
├─ LLM (API_RALF) analiza con prompt especializado:
│  "Eres analista crítico. Verifica falacias, sesgos,
│   credibilidad de fuentes. VEREDICTO: APROBADO/RECHAZADO"
│  
│  (Mismo flujo: ChatOpenAI → Proxy → API_RALF)
│
│  ANÁLISIS GENERADO:
│  """
│  VEREDICTO: APROBADO
│  
│  VERIFICACIONES:
│  ✅ Falacias lógicas: No detectadas
│  ✅ Sesgos: Lenguaje neutral detectado
│  ✅ Fuentes: RPP y El Comercio son confiables
│  ✅ Balance: Presenta datos objetivos sin agenda
│  
│  HECHOS VALIDADOS:
│  - Hospital Rebagliati usa IA (verificado)
│  - 95% precisión (citado en fuente original)
│  - 3 hospitales peruanos (confirmado)
│  
│  LUZ VERDE PARA REDACCIÓN ✅
│  """
│
▼
Socket.IO emit: agent_finish
{"agent": "Analista...", "message": "✅ Calidad aprobada"}
```

**🔄 SI FUERA RECHAZADO:**
```
VEREDICTO: RECHAZADO

PROBLEMAS:
- Falta perspectiva de médicos peruanos
- Solo fuentes de Lima, ¿qué pasa en regiones?

Socket.IO emit: backtracking
{
  "message": "🔄 RECHAZADO: Volviendo a investigar...",
  "feedback": "Buscar testimonios médicos y datos regionales"
}

→ VUELVE A FASE 2 (Iteración 2)
```

---

### ✍️ FASE 4: REDACCIÓN

```
┌────────────────────────────────────────────────────────┐
│ AGENTE: REDACTOR                                       │
└────────────────────────────────────────────────────────┘
│
├─ Socket.IO emit: agent_start
│  {"agent": "Redactor Senior"}
│
├─ Recibe hechos validados del Analista
│
├─ LLM (API_RALF) genera artículo con prompt:
│  "Eres redactor profesional. Estructura: pirámide invertida.
│   Usa SOLO hechos validados. Formato: MARKDOWN"
│  
│  (Mismo flujo: ChatOpenAI → Proxy → API_RALF)
│
│  ARTÍCULO GENERADO (MARKDOWN):
│  """
│  # IA Revoluciona la Medicina en Hospitales Peruanos
│  
│  **Lima, 4 de enero de 2026** - La inteligencia artificial 
│  está transformando el diagnóstico médico en Perú, con tres 
│  hospitales líderes implementando sistemas que alcanzan una 
│  precisión del 95% en la detección temprana de cáncer.
│  
│  ## Tecnología en Acción
│  
│  El Hospital Rebagliati, uno de los más grandes del país, 
│  incorporó un sistema de IA que analiza imágenes médicas 
│  con una velocidad 40% superior a los métodos tradicionales.
│  
│  > "Esta tecnología nos permite salvar más vidas", señala 
│  > el Dr. Carlos Mendoza, jefe de Oncología.
│  
│  ### Datos Clave:
│  
│  - **95%** de precisión en diagnósticos
│  - **3 hospitales** usando IA activamente
│  - **40%** reducción en tiempo de diagnóstico
│  
│  ## Impacto Regional
│  
│  Más allá de Lima, la Clínica San Felipe está probando...
│  
│  ### Fuentes
│  
│  - [RPP Noticias](https://rpp.pe/tecnologia/...)
│  - [El Comercio](https://elcomercio.pe/salud/...)
│  """
│
▼
Socket.IO emit: agent_finish
{"agent": "Redactor Senior", "output": "Artículo completo"}
```

---

### 📤 FASE 5: ENTREGA AL FRONTEND

```
BACKEND (app.py)
│
├─ Crew completada exitosamente
│
├─ Socket.IO emit: generation_complete
│  {
│    "status": "success",
│    "topic": "Avances en IA en medicina peruana",
│    "article": "# IA Revoluciona...\n\n**Lima**...",  ← MARKDOWN
│    "iterations": 1,
│    "session_id": "abc-123-xyz"
│  }
│
▼
FRONTEND (index.html)
│
├─ Evento recibido: generation_complete
│
├─ Ejecuta: displayResult(data.article)
│
├─ RENDERIZADO MARKDOWN → HTML:
│  
│  Input (Markdown):
│  # IA Revoluciona...
│  **Lima, 4 de enero**...
│  
│  Processing:
│  1. Escapar HTML peligroso
│  2. Convertir headers (# → <h1>)
│  3. Convertir bold (**texto** → <strong>)
│  4. Convertir links ([texto](url) → <a>)
│  5. Convertir listas (- item → <li>)
│  6. Convertir código (`code` → <code>)
│  7. Agrupar párrafos (<p>)
│  
│  Output (HTML estilizado):
│  <h1 class="text-5xl font-bold text-[#9D1A10]">
│    IA Revoluciona la Medicina en Hospitales Peruanos
│  </h1>
│  
│  <p class="mb-4 leading-relaxed text-neutral-700">
│    <strong class="font-bold">Lima, 4 de enero de 2026</strong> - 
│    La inteligencia artificial está transformando...
│  </p>
│  
│  <h2 class="text-4xl font-bold border-b-2 border-[#9D1A10]">
│    Tecnología en Acción
│  </h2>
│  
│  <blockquote class="border-l-4 border-[#9D1A10] italic">
│    "Esta tecnología nos permite salvar más vidas"
│  </blockquote>
│  
│  <ul class="my-4">
│    <li class="ml-6 list-disc"><strong>95%</strong> de precisión...</li>
│    <li class="ml-6 list-disc"><strong>3 hospitales</strong>...</li>
│  </ul>
│
├─ Inyecta HTML en <div id="resultArticle">
│
├─ Scroll suave a sección "Intelligence Report"
│
▼
USUARIO VE ARTÍCULO FORMATEADO BELLAMENTE
```

---

## 📊 RESUMEN FLUJO DE DATOS

```
FORMATO POR ETAPA:

1. Frontend Input:     Plain Text
   "Avances en IA medicina peruana"

2. ScraperRalf:        JSON estructurado
   {"results": [...]}

3. LLM Responses:      Plain Text / Reasoning
   "Voy a buscar usando términos..."

4. Investigator Out:   Markdown/Plain Text
   "FUENTES:\n- RPP..."

5. Analyst Out:        Markdown/Plain Text
   "VEREDICTO: APROBADO\n..."

6. Writer Out:         **MARKDOWN**
   "# Título\n\n**Lead**..."

7. Frontend Display:   **HTML Estilizado**
   <h1 class="...">Título</h1>...
```

---

# 🔍 INTEGRACIÓN CON SCRAPERRALF - ANÁLISIS COMPLETO

## 📊 Estado Actual del Sistema

### Configuración Actual (src/tools.py)

```python
# LLAMADA ACTUAL - SIMPLE
response = requests.get(
    "http://127.0.0.1:5000/api/search",
    params={
        "q": "inteligencia artificial medicina",
        "max_results": 5  # ← Por fuente, NO total
    },
    timeout=30  # ← PROBLEMA: Las fuentes locales tardan ~60s
)
```

### ⚠️ PROBLEMA CRÍTICO

**Timeout de 30 segundos VS Tiempo real de ScraperRalf:**

| Fuente | Tipo | Tiempo | Calidad Contenido |
|--------|------|--------|-------------------|
| **La República** | Local | ~45-60s | ⭐⭐⭐⭐⭐ (100% del artículo) |
| **El Comercio** | Local | ~30-45s | ⭐⭐⭐⭐⭐ (JSON-LD completo) |
| **Infobae** | Local | ~60-90s | ⭐⭐⭐⭐⭐ (Browser automation) |
| **NewsAPI** | API Global | ~2-3s | ⭐⭐⭐ (Snippets truncados) |
| **TheNewsAPI** | API Global | ~2-3s | ⭐⭐⭐ (Resúmenes) |

**Resultado actual:** Con `timeout=30`, estás perdiendo:
- ❌ La República (truncado a 30s)
- ❌ Infobae (siempre timeout)
- ✅ El Comercio (a veces pasa)
- ✅ APIs globales (siempre funcionan)

---

## 🎯 ESTRATEGIA DE OPTIMIZACIÓN

### Opción 1: Dos Fases de Búsqueda (Recomendado)

```python
# FASE 1: BÚSQUEDA RÁPIDA (APIs Globales) - 5 segundos
# → Para obtener contexto general y titulares

# FASE 2: BÚSQUEDA PROFUNDA (Scrapers Locales) - 90 segundos
# → Para extraer contenido completo y citas textuales
```

### Opción 2: Búsqueda Paralela Inteligente

ScraperRalf ya usa `ThreadPoolExecutor` internamente, así que todas las fuentes se consultan en paralelo. El tiempo total es el de la fuente **más lenta**.

**Configuración óptima:**
```python
timeout = 90  # Esperar a que Infobae (la más lenta) termine
```

---

## 💡 IMPLEMENTACIÓN RECOMENDADA

### Estrategia 1: "Fast-First, Deep-Later"

Voy a modificar `NewsSearchTool` para hacer dos llamadas:

```python
def _run(self, query: str, max_results: Optional[int] = None) -> str:
    """
    Estrategia de dos fases:
    1. Búsqueda rápida (APIs) para contexto inmediato
    2. Búsqueda profunda (Scrapers) para análisis detallado
    """
    
    # FASE 1: APIs Globales (Rápidas) - 5s timeout
    # ScraperRalf debería tener endpoint: /api/search/fast
    # que solo consulte NewsAPI + TheNewsAPI
    
    fast_results = self._search_fast(query, max_results)
    
    # FASE 2: Scrapers Locales (Lentas) - 90s timeout
    # Endpoint: /api/search/deep (solo El Comercio, La República, Infobae)
    
    deep_results = self._search_deep(query, max_results)
    
    # COMBINAR: Priorizar contenido completo de locales
    return self._merge_results(fast_results, deep_results)
```

### Estrategia 2: "Deep-Only con Timeout Largo"

Más simple pero más lenta:

```python
# Solo llamar a /api/search con timeout largo
response = requests.get(
    endpoint,
    params=params,
    timeout=90  # ← AUMENTADO para permitir Infobae
)
```

---

## 📡 DATOS QUE OBTIENES DE SCRAPERRALF

### Respuesta Típica (5 fuentes en paralelo):

```json
{
  "success": true,
  "total": 15,  // 3 de cada fuente
  "search_time_seconds": 62.5,  // Limitado por Infobae
  "results": [
    // ========================================
    // TIER 1: FUENTES LOCALES (Contenido 100%)
    // ========================================
    {
      "title": "BCR reduce tasa de interés de referencia a 5.75%",
      "content": "El Banco Central de Reserva del Perú (BCRP) decidió reducir en 25 puntos básicos su tasa de interés de referencia, de 6.00% a 5.75%, según informó en su comunicado oficial del jueves 14 de marzo. Esta es la primera reducción en 18 meses, luego de un ciclo de alzas para controlar la inflación que alcanzó un pico de 8.81% en junio de 2022. Según el presidente del BCR, Julio Velarde, 'la decisión refleja la mejora en las expectativas inflacionarias y la recuperación gradual de la actividad económica'. El comunicado del BCRP señala que la inflación interanual de febrero se ubicó en 3.2%, dentro del rango meta de 1% a 3%, con una proyección de cerrar 2024 en 2.5%. Analistas del Banco de Crédito del Perú (BCP) comentaron que...",
      "source": "La República",
      "date": "2024-03-15T10:30:00",
      "url": "https://larepublica.pe/economia/2024/03/15/bcr-reduce-tasa-de-interes-inflacion-peru",
      "image_url": "https://larepublica.pe/resizer/...",
      "method": "CSS Selector"  // Método de extracción
    },
    {
      "title": "Tasa del BCR baja por primera vez desde 2022",
      "content": "Lima, 14 de marzo. La autoridad monetaria del país optó por reducir la tasa de política monetaria (TPM) en un cuarto de punto porcentual, llevándola de 6% a 5.75%, en línea con las proyecciones del mercado. Esta medida busca impulsar el crédito y la inversión privada en un contexto de desaceleración económica global. Según el análisis de la Sociedad Nacional de Industrias (SNI), esta reducción podría traducirse en menores tasas de interés para préstamos empresariales y créditos hipotecarios en los próximos meses. El documento del BCRP destaca que...",
      "source": "El Comercio",
      "date": "2024-03-14T18:45:00",
      "url": "https://elcomercio.pe/economia/peru/bcr-tasa-interes-referencia-reduccion-inflacion-noticia/",
      "image_url": "https://img.elcomercio.pe/...",
      "method": "JSON-LD"
    },
    {
      "title": "Banco Central recorta tasa de referencia ante mejora inflacionaria",
      "content": "La directiva del Banco Central de Reserva (BCR) aprobó este jueves reducir la tasa de interés de política monetaria de 6.00% a 5.75%, marcando un cambio en la postura restrictiva que mantuvo desde mediados de 2022. En su comunicado, el BCR argumenta que 'la convergencia de la inflación hacia el rango meta, junto con la mejora de las expectativas de los agentes económicos, permite una postura menos restrictiva'. Expertos consultados señalan que...",
      "source": "Infobae",
      "date": "2024-03-14T20:15:00",
      "url": "https://www.infobae.com/peru/2024/03/14/bcr-reduce-tasa-interes/",
      "image_url": "https://www.infobae.com/new-resizer/...",
      "method": "Browser Automation"
    },

    // ========================================
    // TIER 2: APIs GLOBALES (Resúmenes)
    // ========================================
    {
      "title": "Peru's Central Bank Cuts Interest Rate to 5.75%",
      "content": "Peru's central bank reduced its benchmark interest rate by 25 basis points to 5.75% on Thursday, the first cut in 18 months...",  // ← TRUNCADO
      "source": "NewsAPI",
      "date": "2024-03-14T21:00:00",
      "url": "https://www.reuters.com/markets/americas/peru-central-bank-rate-cut/",
      "image_url": null,
      "method": "External API"
    },
    {
      "title": "BCR de Perú reduce tasa de referencia",
      "content": "El Banco Central de Reserva del Perú redujo su tasa de interés de referencia a 5.75%, según anunció hoy...",  // ← SNIPPET
      "source": "TheNewsAPI",
      "date": "2024-03-14T19:30:00",
      "url": "https://www.bloomberg.com/...",
      "image_url": "https://assets.bwbx.io/...",
      "method": "External API"
    }
  ]
}
```

### 📋 Comparación de Contenido

| Campo | Local (La República) | API Global (NewsAPI) |
|-------|---------------------|---------------------|
| **title** | Completo | Completo |
| **content** | **2,500+ caracteres** (artículo completo) | **~200 caracteres** (snippet) |
| **source** | "La República" | "NewsAPI" |
| **date** | Fecha exacta de publicación | Fecha de indexación (puede diferir) |
| **url** | Link directo al artículo | Link original (puede requerir paywall) |
| **image_url** | URL de imagen optimizada | Puede ser null |
| **method** | "CSS Selector" / "JSON-LD" / "Browser" | "External API" |

---

## 🔧 OPTIMIZACIONES PROPUESTAS

### 1. Aumentar Timeout (Solución Inmediata)

```python
# EN: src/tools.py
response = requests.get(
    endpoint,
    params=params,
    timeout=90,  # ← CAMBIAR DE 30 A 90
    headers={"User-Agent": "MultiAgent-NewsSystem/1.0"},
)
```

**Pros:**
- ✅ Simple, un cambio de 1 línea
- ✅ Obtienes las 5 fuentes (locales + APIs)
- ✅ Contenido completo para análisis profundo

**Contras:**
- ❌ El Investigator esperará ~60-90s por cada búsqueda
- ❌ Si Infobae falla, todo el request se cuelga

---

### 2. Búsqueda Adaptativa (Avanzada)

```python
def _run(self, query: str, max_results: Optional[int] = None) -> str:
    """Búsqueda con fallback automático"""
    
    # Intentar primero con timeout largo (obtener todo)
    try:
        return self._search_with_timeout(query, max_results, timeout=90)
    except requests.Timeout:
        logger.warning("⏱️ Timeout en búsqueda profunda, intentando rápida...")
        # Fallback: Solo APIs rápidas
        return self._search_with_timeout(query, max_results, timeout=10)
```

---

### 3. Endpoint Selectivo en ScraperRalf (Requiere modificar tu API)

Crear nuevos endpoints en tu ScraperRalf:

```python
# EN TU SCRAPERRALF: app.py

@app.route('/api/search/fast')
def search_fast():
    """Solo APIs globales: NewsAPI + TheNewsAPI"""
    # Tiempo: ~5 segundos
    # Usa solo: newsapi.py + thenewsapi.py
    pass

@app.route('/api/search/deep')
def search_deep():
    """Solo scrapers locales: El Comercio + La República + Infobae"""
    # Tiempo: ~60-90 segundos
    # Usa solo: elcomercio.py + larepublica.py + infobae.py
    pass

@app.route('/api/search/hybrid')
def search_hybrid():
    """Primero APIs (5s), luego scrapers en background"""
    # Retorna inmediatamente con APIs
    # Scrapers se agregan vía webhooks o polling
    pass
```

Luego en MultiAgent:

```python
# Fase 1: Contexto rápido
fast_response = requests.get(
    "http://127.0.0.1:5000/api/search/fast",
    params={"q": query, "max_results": 3},
    timeout=10
)

# Fase 2: Contenido profundo (solo si el Analista lo requiere)
if analysis_requires_deep_content:
    deep_response = requests.get(
        "http://127.0.0.1:5000/api/search/deep",
        params={"q": query, "max_results": 2},
        timeout=90
    )
```

---

## 🎯 RECOMENDACIÓN FINAL

### Para Producción Inmediata:

**Opción Simple:** Aumentar timeout a 90s

```python
# src/tools.py - línea 123
timeout=90  # Cambiar de 30 a 90
```

**Justificación:**
- El Investigator solo busca **1 vez** por iteración
- Esperar 90s para obtener contenido completo es aceptable
- El LLM necesita **citas textuales** que solo las fuentes locales proveen
- Las APIs globales darán snippets truncados que no sirven para análisis

### Para Futuro (Optimización Avanzada):

**Opción Avanzada:** Implementar búsqueda en dos fases

1. Modificar ScraperRalf para tener `/api/search/fast` y `/api/search/deep`
2. Llamar primero a `fast` (5s) para obtener contexto
3. El LLM decide si necesita profundizar
4. Si es necesario, llamar a `deep` (90s)

---

## 📊 COMPARACIÓN DE RENDIMIENTO

### Escenario: "Buscar 'crisis económica Perú 2024'"

#### Configuración Actual (timeout=30s):
```
Tiempo total: 30s (timeout)
Resultados obtenidos:
✅ NewsAPI: 3 artículos (snippets)
✅ TheNewsAPI: 3 artículos (snippets)
⚠️ El Comercio: 2 artículos (parcial, cortado a 30s)
❌ La República: 0 artículos (timeout)
❌ Infobae: 0 artículos (timeout)

Total útil: 8 artículos con contenido limitado
```

#### Configuración Propuesta (timeout=90s):
```
Tiempo total: 75s (máximo de Infobae)
Resultados obtenidos:
✅ NewsAPI: 3 artículos (snippets) - 3s
✅ TheNewsAPI: 3 artículos (snippets) - 3s
✅ El Comercio: 3 artículos (completos) - 35s
✅ La República: 3 artículos (completos) - 50s
✅ Infobae: 3 artículos (completos) - 75s

Total útil: 15 artículos con 9 de contenido COMPLETO
```

**Ganancia:**
- +87% más artículos
- +9 fuentes con texto completo (antes 0)
- Tiempo extra: +45 segundos (aceptable para calidad)

---

# 📋 CHEATSHEET - Referencia Rápida

## Comandos Esenciales

### Instalación
```bash
# Windows
install.bat

# Linux/Mac
chmod +x install.sh
./install.sh

# Manual
pip install -r requirements.txt
```

### Verificación
```bash
python setup_check.py
```

### Ejecución
```bash
# Con dashboard (recomendado)
python app.py

# Solo CLI
python test_simple.py "Tu tema aquí"
```

## URLs y Puertos

| Servicio | URL | Propósito |
|----------|-----|-----------|
| Dashboard | http://localhost:8080 | Interfaz visual |
| API REST | http://localhost:8080/api/* | Endpoints |
| Socket.IO | ws://localhost:8080/agents | Eventos en vivo |
| ScraperRalf | http://localhost:5000 | Búsqueda de noticias |
| API_RALF | (configurar en .env) | LLM personalizado |

## Estructura de Archivos

```
📁 MultiAgent_AI_R/
├── 📄 .env                 ← Configuración (EDITAR)
├── 🚀 app.py               ← Servidor principal
├── 🧪 test_simple.py       ← Test rápido CLI
├── 🔍 setup_check.py       ← Verificador
├── 📦 requirements.txt     ← Dependencias
├── 📖 README.md            ← Documentación principal
├── 🚦 QUICKSTART.md        ← Guía rápida
├── 🏗️ ARCHITECTURE.md      ← Arquitectura detallada
│
├── 📁 src/
│   ├── llm_config.py       ← Config LLM
│   ├── tools.py            ← Herramientas
│   ├── callbacks.py        ← Eventos
│   └── crew.py             ← Agentes y lógica
│
└── 📁 templates/
    └── index.html          ← Dashboard UI
```

## Variables de Entorno (.env)

```bash
# CRÍTICO: Configurar antes de usar
DOMINIO_API_RALF=tu-dominio.com
RALF_API_KEY=opcional
RALF_MODEL_NAME=ralf-mixed-model

# Opcionales
SCRAPER_BASE_URL=http://localhost:5000
FLASK_PORT=8080
MAX_ITERATIONS=5
```

## Agentes y Temperatures

| Agente | Role | Temperature | Herramientas |
|--------|------|-------------|--------------|
| Manager | Coordinador | 0.6 | - |
| Investigador | Búsqueda | 0.3 | NewsSearchTool |
| Analista | Verificación | 0.5 | - |
| Redactor | Escritura | 0.8 | - |

## API REST Endpoints

### POST /api/generate
```bash
curl -X POST http://localhost:8080/api/generate \
  -H "Content-Type: application/json" \
  -d '{"topic": "Inteligencia artificial en medicina"}'
```

### GET /api/result/{session_id}
```bash
curl http://localhost:8080/api/result/{session_id}
```

### GET /api/health
```bash
curl http://localhost:8080/api/health
```

## Eventos Socket.IO

### Conectar
```javascript
const socket = io('http://localhost:8080/agents');
```

### Unirse a sesión
```javascript
socket.emit('join_session', {session_id: 'xxx'});
```

### Escuchar eventos
```javascript
socket.on('agent_start', (data) => {
  console.log('Agente:', data.agent);
  console.log('Tarea:', data.task);
});

socket.on('generation_complete', (data) => {
  console.log('Artículo:', data.article);
});
```

## Troubleshooting Rápido

### "No se puede importar X"
```bash
pip install -r requirements.txt --upgrade
```

### "API_RALF no conecta"
1. Verificar DOMINIO_API_RALF en .env
2. Probar: `curl https://tu-dominio.com/v1`

### "ScraperRalf no disponible"
1. Verificar que corre en puerto 5000
2. Probar: `curl http://localhost:5000/api/search?q=test`

### "Socket.IO no conecta"
1. Abrir F12 en navegador → Console
2. Verificar URL correcta
3. Deshabilitar firewall temporalmente

## Personalización

### Cambiar temperature de agente
```python
# En src/crew.py
def get_investigator_llm():
    return config.get_llm(temperature=0.3)  # ← Cambiar
```

### Agregar nueva herramienta
```python
# En src/tools.py
class MiHerramienta(BaseTool):
    name = "mi_tool"
    description = "..."
    
    def _run(self, input: str) -> str:
        # Tu lógica aquí
        return resultado
```

### Modificar personalidad
```python
# En src/crew.py → create_*_agent()
backstory=(
    "Tu nueva personalidad aquí..."
)
```

## Logs y Debug

### Ver logs detallados
```bash
# Flask muestra logs automáticamente
python app.py

# O en nivel DEBUG
export FLASK_DEBUG=True  # Linux/Mac
set FLASK_DEBUG=True     # Windows
python app.py
```

### Logs de agentes
Los agentes ya tienen `verbose=True`, mostrarán pensamiento en consola.

## Testing

### Test completo
```bash
python test_simple.py "Avances en IA"
```

### Test por componente
```bash
# LLM
python src/llm_config.py

# Herramientas
python src/tools.py

# Callbacks
python src/callbacks.py

# Crew completa
python src/crew.py
```

## Teoría Rápida (AIMA)

### HTN (Cap. 11.3)
- Tarea compuesta: "Producir Noticia"
- Descomposición: Buscar → Validar → Redactar

### Vigilancia (Cap. 12.5)
- Analista verifica precondiciones
- Si falla → replanificación (loop)

### Multiagente (Cap. 17)
- Coordinación jerárquica (Manager-Worker)
- Comunicación por artefactos (no negociación)

## Performance

### Tiempo promedio por artículo
- 1-3 minutos (depende de LLM y red)

### Optimizaciones posibles
1. Caché de búsquedas repetidas
2. Paralelizar búsquedas (múltiples queries)
3. Ajustar max_iterations (menor = más rápido)

## Seguridad

### Producción
```bash
# Cambiar en .env
FLASK_SECRET_KEY=clave-super-segura-aleatoria
FLASK_DEBUG=False

# Configurar CORS específico en app.py
CORS(app, origins=['https://tu-dominio.com'])
```

---

# 🔧 RESOLUCIÓN DE PROBLEMAS CONOCIDOS

## Problema 1: Timeout del Investigador ⏱️

### Síntoma
El Investigador no esperaba los 60-70s necesarios para que ScraperRalf completara la búsqueda, resultando en datos incompletos.

### Causa Raíz
El LLM tenía un timeout de 60s, pero ScraperRalf necesita ~67s para completar todas las fuentes (especialmente las locales).

### Solución Implementada ✅

**Archivo modificado:** [src/llm_config.py](src/llm_config.py#L85)

```python
# ANTES
ChatOpenAI(..., timeout=60)

# DESPUÉS  
ChatOpenAI(..., timeout=120, max_retries=3)  # Suficiente para ScraperRalf (~67s)
```

**Justificación:**
- ScraperRalf tarda ~67s en el mejor caso
- Timeout de 120s da margen de 53s adicionales
- Cubre casos donde Infobae tarda hasta 90s

### Verificación

Ejecutar el sistema y verificar en los logs:

```
🔴🔴🔴 INVESTIGADOR LLAMÓ A LA HERRAMIENTA NewsSearchTool 🔴🔴🔴
⏳ ESPERANDO RESPUESTA DE SCRAPERRALF... (esto puede tardar 60-70 segundos)

[... espera de 60-70 segundos ...]

🟢🟢🟢 HERRAMIENTA COMPLETADA - DATOS RECIBIDOS DE SCRAPERRALF 🟢🟢🟢
⏱️ Tiempo de espera: 67.42 segundos
📊 TIER 1 (Fuentes Locales): 13 artículos
```

---

## Problema 2: "Esquizofrenia Temporal" 🕰️

### Síntoma
El sistema fallaba con error **"Máximo de iteraciones alcanzado sin aprobación"** porque el Analista rechazaba noticias de 2026 como "FALACIAS DE FUTURO CONSUMADO".

### Causa Raíz
- ScraperRalf devolvía noticias fechadas "4 de enero de 2026" (fecha real)
- El Analista creía que estaba en "Mayo de 2024"
- Rechazaba todas las noticias como temporalmente imposibles

### Solución Implementada ✅

**Propagación de fecha dinámica en todo el sistema:**

```python
# app.py
from datetime import datetime
current_date = datetime.now().strftime("%Y-%m-%d")  # 2026-01-04

# Pasada a todos los agentes
def create_bias_analyst_agent(current_date):
    return Agent(
        goal=f"⚠️ CONTEXTO TEMPORAL: HOY ES {current_date}. Validar credibilidad...",
        backstory=f"📅 FECHA ACTUAL: {current_date} - Esta es tu realidad temporal..."
    )
```

**Flujo de fecha:**
```
app.py → generate_news_article(topic, session_id, current_date)
       → NewsCrew.run(topic, current_date)
       → create_bias_analyst_agent(current_date)
       → create_investigation_task(agent, topic, current_date)
```

### Verificación

Los logs deben mostrar:

```
📅 CONTEXTO TEMPORAL: Hoy es 2026-01-04
🔍 ANALISTA - FECHA DE CONTEXTO: 2026-01-04
✅ Analista veredicto: APROBADO  ← No rechaza por fechas
```

---

## Problema 3: Artículos Desordenados en Frontend 📰

### Síntoma
Los artículos se mostraban como texto plano sin la estructura visual de una revista profesional.

### Soluciones Implementadas ✅

#### A) Parser Markdown Mejorado (15+ mejoras)

**Archivo:** [templates/index.html](templates/index.html) - Función `displayResult()`

**Mejoras clave:**

1. **Headers jerárquicos** con tipografía profesional:
   - H1: `text-4xl md:text-6xl font-black text-[#9D1A10]`
   - H2: `text-2xl md:text-3xl border-b-2 border-[#9D1A10]`
   - H3: `text-xl md:text-2xl border-l-4 border-[#9D1A10]`

2. **Lead destacado** (primer párrafo en negrita):
   ```html
   text-xl md:text-2xl font-semibold border-l-4 border-[#9D1A10] bg-neutral-50
   ```

3. **Blockquotes estilo revista**:
   ```html
   border-l-4 border-[#9D1A10] bg-neutral-50 pl-6 italic text-lg shadow-sm
   ```

4. **Links con indicador externo**:
   - Color corporativo `#9D1A10`
   - Ícono "↗" para links externos
   - Hover con `decoration-wavy`

5. **Código inline y bloques**:
   - Inline: `bg-red-50 text-[#9D1A10] border border-red-100`
   - Bloques: `bg-neutral-900 text-green-400 rounded-xl shadow-lg`

6. **Párrafos justificados** tipo revista:
   ```html
   text-lg leading-relaxed text-neutral-700 text-justify mb-6
   ```

#### B) Instrucciones Detalladas para Redactor

**Archivo:** [src/crew.py](src/crew.py) - Función `create_writing_task()`

**Plantilla estructurada completa:**

```markdown
# TÍTULO (máx 12 palabras)

**[LEAD EN NEGRITA: 2-3 oraciones]**

## Contexto e Introducción
...

> "Cita textual"
> — Autor, Cargo

## Desarrollo Principal

### Primer Aspecto
- **Dato 1**: Explicación
- **Dato 2**: Contexto

---

## Análisis de Sesgos
...

## Conclusión
...
```

**Checklist de calidad obligatorio:**
```
✅ UN SOLO H1
✅ Lead en negrita al inicio
✅ Mínimo 4 secciones H2
✅ Subsecciones H3
✅ 2-3 blockquotes
✅ Listas con viñetas
✅ 900-1400 palabras
✅ Tono periodístico profesional
```

**Referencias de estilo:**
- The New York Times
- El País
- The Guardian
- Le Monde

### Verificación

El artículo final debe verse como una publicación profesional con:
- Tipografía clara y jerárquica
- Espaciado apropiado entre secciones
- Citas destacadas visualmente
- Lead impactante al inicio
- Estructura lógica y fluida

---

## Diagnóstico de Timeout de ScraperRalf 🔍

### Verificación de Tiempos

Para confirmar que ScraperRalf está devolviendo datos completos:

**Script de test:**
```bash
python test_scraper_timing.py
```

**Resultado esperado:**
```
✅ ScraperRalf responde en ~67.89 segundos
✅ Fuentes Tier 1 (locales): 13 artículos
✅ Contenido promedio: 3,862 caracteres
```

### Logging Mejorado

**Archivo:** [src/tools.py](src/tools.py)

**Salida detallada:**
```
🔎 INICIO BÚSQUEDA: 'tema' (max: 5 por fuente)
⏱️ Timestamp: 17:41:25

[... espera ...]

✅ RESPUESTA RECIBIDA en 67.89 segundos
⏱️ Inicio: 17:41:25 → Fin: 17:42:33

📊 ANÁLISIS DE DISTRIBUCIÓN POR TIER:
   🟢 TIER 1 (Fuentes Locales): 13 artículos
   🟡 TIER 2 (APIs Globales): 0 artículos
   📏 Longitud promedio Tier 1: 3862 caracteres
```

### Alerta de Timeout

Si solo se reciben APIs globales:

```
⚠️ ADVERTENCIA: Solo APIs globales recibidas. Scrapers locales no respondieron.
   Posibles causas:
   1. ScraperRalf tiene timeout interno < 90s
   2. Scrapers locales están fallando
   3. Camoufox no instalado: 'camoufox fetch'
```

---

## Resumen de Mejoras Implementadas 🎯

| Problema | Solución | Archivo Modificado | Estado |
|----------|----------|-------------------|--------|
| Timeout LLM (60s vs 67s) | Aumentar a 120s | [src/llm_config.py](src/llm_config.py#L85) | ✅ |
| Esquizofrenia temporal | Fecha dinámica en agentes | [src/crew.py](src/crew.py), [app.py](app.py) | ✅ |
| Artículos desordenados | Parser MD + instrucciones | [templates/index.html](templates/index.html), [src/crew.py](src/crew.py) | ✅ |
| Logging insuficiente | Timestamps + distribución | [src/tools.py](src/tools.py), [src/callbacks.py](src/callbacks.py) | ✅ |
| max_iter bajo | Aumentar de 3 a 5 | [src/crew.py](src/crew.py#L105) | ✅ |
| **Ceguera Temporal** | Grounding temporal con filtrado | [src/crew.py](src/crew.py) | ✅ |
| **Sesgo Regional** | Protocolo búsqueda estructurada (SOP) | [src/crew.py](src/crew.py) | ✅ |
| **Falta validación lógica** | Sanity Check matemático/temporal | [src/crew.py](src/crew.py) | ✅ |

**Tiempo promedio por artículo:** 1-3 minutos (incluye espera de ScraperRalf)

**Calidad esperada:** Artículos con estructura profesional, datos verificados y formato de revista digital.

---

# 📚 Documentación Completa

## Verificación de Timeout y ScraperRalf

### ✅ Verificación Técnica del Timeout

El sistema está **correctamente configurado** para esperar la respuesta completa de ScraperRalf.

#### Configuración en `src/tools.py` (Líneas 127-145)

```python
# Timeout de 90s para permitir que scrapers locales completen
# ScraperRalf ejecuta las 5 fuentes en paralelo:
# - APIs globales (NewsAPI, TheNewsAPI): ~3-5s
# - El Comercio (JSON-LD): ~30-45s
# - La República (CSS): ~45-60s
# - Infobae (Camoufox): ~60-90s
response = requests.get(
    endpoint,
    params=params,
    timeout=90,  # Python BLOQUEA aquí hasta recibir respuesta completa
    headers={"User-Agent": "MultiAgent-NewsSystem/1.0"},
)
```

#### ¿Qué significa `timeout=90`?

**Comportamiento de `requests.get(timeout=90)`:**

1. **Python BLOQUEA la ejecución** del código en esta línea
2. **Espera hasta 90 segundos** a que ScraperRalf devuelva la respuesta completa
3. **NO continúa** hasta que:
   - ScraperRalf devuelva el JSON completo con todas las fuentes, **O**
   - Pasen 90 segundos (entonces lanza `requests.Timeout`)

**¿El agente Investigador espera?**  
✅ **SÍ**. El código Python está bloqueado en `response = requests.get(...)` hasta que ScraperRalf complete.

#### Flujo de Ejecución Paso a Paso

```
┌─────────────────────────────────────────────────────────────────┐
│ T=0s: Investigador llama NewsSearchTool._run()                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ T=0s: Python ejecuta:                                           │
│   response = requests.get(                                      │
│       "http://127.0.0.1:5000/api/search",                      │
│       params={"q": "tema", "max_results": 5},                  │
│       timeout=90                                                │
│   )                                                             │
│                                                                 │
│ ⚠️ EL CÓDIGO SE DETIENE AQUÍ Y ESPERA ⚠️                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ T=0-3s: ScraperRalf lanza 5 threads en paralelo:               │
│   • Thread 1: NewsAPI       → Responde en ~3s                  │
│   • Thread 2: TheNewsAPI    → Responde en ~3s                  │
│   • Thread 3: El Comercio   → Responde en ~35s                 │
│   • Thread 4: La República  → Responde en ~50s                 │
│   • Thread 5: Infobae       → Responde en ~75s (Camoufox)      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ ⏳ Python/Investigador ESPERANDO...
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ T=75s: ScraperRalf consolida resultados de los 5 threads      │
│   • NewsAPI: 3 artículos (snippets)                            │
│   • TheNewsAPI: 3 artículos (snippets)                         │
│   • El Comercio: 3 artículos completos (JSON-LD)               │
│   • La República: 3 artículos completos (CSS)                  │
│   • Infobae: 3 artículos completos (Camoufox)                  │
│                                                                 │
│ Total: 15 artículos                                             │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ T=75s: ScraperRalf devuelve JSON completo                      │
│   {                                                             │
│     "results": [                                                │
│       { "source": "La República", "content": "..." },          │
│       { "source": "El Comercio", "content": "..." },           │
│       { "source": "Infobae", "content": "..." },               │
│       ...                                                       │
│     ]                                                           │
│   }                                                             │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ T=75s: Python CONTINÚA la ejecución                            │
│   response.raise_for_status()  # OK                            │
│   data = response.json()       # Parsea JSON completo          │
│                                                                 │
│ ✅ Investigador ahora tiene 15 artículos completos             │
└─────────────────────────────────────────────────────────────────┘
```

#### Clasificación por Tiers

**Líneas 152-169 en `src/tools.py`:**

```python
# Tier 1: Fuentes locales con contenido completo
is_deep_source = source in ["La República", "El Comercio", "Infobae"]

# Tier 2: APIs globales con snippets
is_api_source = source in ["NewsAPI", "TheNewsAPI"]

formatted_results.append({
    "id": idx,
    "title": item.get("title", "Sin título"),
    "content": content,
    "source": source,
    "url": item.get("url", ""),
    "date": item.get("date", ""),
    "tier": "deep" if is_deep_source else ("api" if is_api_source else "unknown"),
    "content_length": len(content),
    "extraction_method": item.get("method", "unknown"),
})
```

**Resumen en JSON de respuesta (Líneas 188-194):**

```python
return json.dumps({
    "status": "success",
    "query": query,
    "total_results": len(formatted_results),
    "deep_sources_count": sum(1 for r in formatted_results if r["tier"] == "deep"),
    "api_sources_count": sum(1 for r in formatted_results if r["tier"] == "api"),
    "results": formatted_results,
})
```

---

## 🚀 Mejoras Críticas Implementadas (Enero 2026)

### 1. Grounding Temporal - Solución a "Ceguera Temporal"

**Problema Original:**
El agente recuperaba artículos antiguos (2021-2022) que especulaban sobre eventos futuros ya ocurridos.

**Solución Implementada:**

```python
# En create_investigator_agent(current_date: str = "")
if not current_date:
    from datetime import datetime
    current_date = datetime.now().strftime("%Y-%m-%d")

# Calcular umbral de antigüedad (hace 24 meses)
threshold_date = (datetime.strptime(current_date, "%Y-%m-%d") - timedelta(days=730)).strftime("%Y-%m-%d")

goal=(
    f"📅 CONTEXTO TEMPORAL CRÍTICO:\n"
    f"HOY ES: {current_date}\n"
    f"UMBRAL DE ANTIGÜEDAD: {threshold_date} (hace 24 meses)\n\n"
    f"❌ FILTRO TEMPORAL ABSOLUTO:\n"
    f"- RECHAZAR automáticamente cualquier artículo con fecha ANTERIOR a {threshold_date}\n"
    f"- Si una fuente especula sobre eventos YA OCURRIDOS, DESCARTARLA\n"
)
```

**Resultado:**
- ✅ El agente descarta artículos de hace más de 24 meses
- ✅ Prioriza información de los últimos 6 meses
- ✅ Ignora fuentes que hablan especulativamente de eventos ya ocurridos

### 2. Protocolo de Búsqueda Estructurada (SOP) - Solución a "Sesgo Regional"

**Problema Original:**
El agente solo buscaba fuentes peruanas/argentinas para temas globales (ej. Mundial FIFA).

**Solución Implementada:**

```python
"📋 PROTOCOLO DE BÚSQUEDA ESTRUCTURADA (SOP) - 4 PASOS OBLIGATORIOS:\n\n"
"PASO 1: BÚSQUEDA DE FUENTES OFICIALES\n"
"   ➤ Query específica: '[tema] official statement'\n"
"   ➤ Buscar: FIFA.com, UN.org, Gov.pe, sitios gubernamentales\n\n"
"PASO 2: BÚSQUEDA EN AGENCIAS INTERNACIONALES\n"
"   ➤ Query: '[tema] Reuters' o '[tema] AP'\n"
"   ➤ CRÍTICO: Si el tema es global y solo encuentras fuentes peruanas, BUSCAR MÁS\n\n"
"PASO 3: BÚSQUEDA EN MEDIOS LOCALES\n"
"   ➤ Query: '[tema]' (general)\n"
"   ➤ Fuentes: La República, El Comercio\n\n"
"PASO 4: SANITY CHECK MATEMÁTICO Y LÓGICO\n"
```

**Triangulación Obligatoria:**
```python
"🎯 OBJETIVO PRINCIPAL:\n"
"Implementar TRIANGULACIÓN DE FUENTES obligatoria:\n"
"1. Al menos 1 fuente OFICIAL (FIFA, gobiernos, instituciones)\n"
"2. Al menos 1 agencia INTERNACIONAL (Reuters, AP, AFP, EFE)\n"
"3. Al menos 1 medio LOCAL (La República, El Comercio, etc.)\n"
```

**Resultado:**
- ✅ El agente ejecuta 3 búsquedas separadas
- ✅ Evita el sesgo de un solo país/región
- ✅ Garantiza balance de perspectivas

### 3. Sanity Check Matemático - Solución a "Falta de Validación Lógica"

**Problema Original:**
El agente pasaba datos matemáticamente inconsistentes (ej. "12 grupos → 24 clasifican, pero octavos de 16").

**Solución Implementada:**

```python
"🔍 SANITY CHECK FINAL (OBLIGATORIO):\n"
"Antes de finalizar, LEE TODO tu informe y verifica:\n\n"
"1. COHERENCIA NUMÉRICA:\n"
"   - Si mencionas estadísticas relacionadas, verifica que sean coherentes\n"
"   - Formato de torneos: ¿los números tienen sentido? (octavos = 16, cuartos = 8)\n\n"
"2. COHERENCIA TEMPORAL:\n"
"   - ¿Todas las fuentes son posteriores al umbral de antigüedad?\n"
"   - ¿Hay artículos especulando sobre eventos ya pasados?\n\n"
"3. COHERENCIA GEOGRÁFICA:\n"
"   - Si es tema global, ¿tienes fuentes de al menos 2 regiones/países?\n\n"
"4. CONTRADICCIONES LÓGICAS:\n"
"   - ¿Alguna fuente contradice a otra en datos clave?\n"
"   - Si sí: Buscar una tercera fuente autoritativa para desempatar\n"
```

**Ejemplo Educativo Incluido:**
```python
"Tema: Mundial de Fútbol 2026\n"
"Dato encontrado: '12 grupos de 4 equipos'\n"
"Sanity Check: 12 × 4 = 48 equipos total\n"
"Dato encontrado: 'Pasan los 2 primeros de cada grupo'\n"
"Sanity Check: 12 × 2 = 24 equipos a octavos\n"
"Dato encontrado: 'Octavos de final con 16 equipos'\n"
"⚠️ CONTRADICCIÓN DETECTADA: 24 ≠ 16\n"
"Acción: Buscar '[tema] formato octavos de final' para aclarar\n"
```

**Resultado:**
- ✅ El agente valida la coherencia numérica antes de finalizar
- ✅ Detecta contradicciones lógicas entre fuentes
- ✅ Busca información adicional cuando encuentra inconsistencias

### 4. Mejoras en el Analista de Sesgos

```python
"5. VALIDACIÓN DE COHERENCIA MATEMÁTICA Y LÓGICA (NUEVO):\n"
"   - Si hay estadísticas relacionadas, ¿son coherentes?\n"
"   - Si se mencionan fases de torneo, ¿los números cuadran?\n\n"
"6. TRIANGULACIÓN DE FUENTES (NUEVO):\n"
"   - ¿Hay al menos 1 fuente oficial/autoritativa?\n"
"   - ¿Hay al menos 1 fuente internacional para temas globales?\n"
"   - Si el tema es global y solo hay fuentes locales → RECHAZAR por sesgo geográfico\n\n"
"7. VERIFICACIÓN TEMPORAL:\n"
"   - ¿Las fuentes son recientes (últimos 24 meses preferentemente)?\n"
```

**Ejemplos de Rechazo Obligatorio:**
```python
"❌ 'Solo fuentes peruanas/argentinas sobre tema global (Mundial FIFA)'\n"
"   → Requiere: Buscar fuentes de FIFA.com, Reuters, AP\n"
"❌ 'Contradicción: 12 grupos → 24 clasifican, pero dice octavos de 16'\n"
"   → Requiere: Buscar 'formato oficial Mundial 2026 FIFA'\n"
```

---

## 🧪 Testing y Verificación

### Test de Timing del Scraper

```bash
python test_scraper_timing.py
```

**Qué verifica:**
1. ✅ Conectividad con ScraperRalf
2. ⏱️ Tiempo de espera (esperado: 45-90s)
3. 📊 Distribución de fuentes (Tier 1 vs Tier 2)
4. 📏 Longitud de contenido (>1000 chars para Tier 1)

**Resultados esperados:**
```
🎉 CONCLUSIÓN: El sistema está funcionando CORRECTAMENTE
   • El timeout de 90s es respetado
   • Las fuentes locales están entregando contenido completo
   • El Investigator recibirá información de calidad
```

### Logging en Tiempo Real

Cuando el Investigador ejecuta una búsqueda:

```
🔎 Buscando: 'tema' (max: 5 resultados)
[... espera ~75 segundos ...]
✅ Encontrados 15 artículos
📊 Distribución: 9 fuentes locales (deep), 6 APIs globales
```

**Interpretación:**
- **9 fuentes locales:** 3 artículos × 3 fuentes (La República, El Comercio, Infobae)
- **6 APIs globales:** 3 artículos × 2 APIs (NewsAPI, TheNewsAPI)

⚠️ Si ves `0 fuentes locales (deep)` → Indica timeout o fallo en scrapers locales

---

# 🧪 Fundamentos Teóricos (Russell & Norvig - AIMA)

- **Planificación HTN** (Cap. 11.3)
- **Vigilancia de Ejecución** (Cap. 12.5)
- **Arquitecturas Multiagente** (Cap. 17)

Desarrollado con ❤️ usando CrewAI y Planificación HTN

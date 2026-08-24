# PLAN DE IMPLEMENTACIÓN & OPENSPEC: CLASIFICADOR DE CORREOS

**Proyecto:** Microservicio Django de Clasificación y Triage de Correos (Modo JSON / No-DB)  
**Versión de Especificación:** OpenSpec v1.0  
**Fecha:** 24 de Agosto de 2026  
**Estado:** Listo para Desarrollo  

---

## 1. Problema
El personal administrativo enfrenta episodios recurrentes de saturación y estrés operativo debido a la acumulación masiva de correos electrónicos no leídos y solicitudes desordenadas [cite: 2]. Las bandejas de entrada tradicionales no cuentan con una jerarquización contextual ni discriminan la urgencia real frente a casos históricos, lo que genera retrasos en tareas críticas (bloqueos operativos, vencimiento de plazos, cortes de servicio) y pérdida de tiempo en lectura de correos meramente informativos o con cadenas de texto redundantes [cite: 2].

---

## 2. Solución
Desarrollar un microservicio desacoplado en **Python y Django** que opere **sin base de datos relacional ni ORM (`DATABASES = {}`)**, procesando la información directamente en memoria y mediante el archivo **`datos.json`** en la raíz del proyecto [cite: 2].

El sistema:
1. Recibe el correo en formato JSON a través de una vista (`core/views.py`) [cite: 2].
2. Aplica un pipeline de sanitización (eliminación de HTML, firmas, disclaimers y respuestas anidadas) implementado de forma modular en `solucion.py` [cite: 2].
3. Realiza una búsqueda de contexto RAG en memoria comparando el mensaje contra el dataset `datos.json` mediante vectorización TF-IDF y similitud de coseno (`solucion.py`) [cite: 2].
4. Consulta un modelo LLM local (Ollama) o activa una heurística de contingencia inmediata para generar un resumen ejecutivo, un puntaje de prioridad (1 al 5), una categoría operativa y una acción sugerida [cite: 2].
5. Provee tanto una API JSON como una interfaz web básica de visualización a través de `core/templates/resumen.html`.

---

## 3. Alcance

### Enfoque Arquitectural
* **Stateless Backend:** Proyecto Django estándar (`miproyecto/` como directorio de configuración y `core/` como aplicación principal) configurado sin migraciones SQL [cite: 2].
* **Persistencia en `datos.json`:** Carga y lectura del archivo de datos en la raíz para indexación vectorial en memoria [cite: 2].
* **Modularidad Centralizada:** Lógica de negocio, RAG, sanitización y cliente LLM encapsulados en `solucion.py`, consumidos directamente por `core/views.py` y `core/apps.py`.
* **Privacidad On-Premise & Resiliencia:** Procesamiento local con fallback determinista en caso de desconexión del LLM [cite: 2].

---

## 4. MoSCoW

| Categoría | Requerimientos |
| :--- | :--- |
| **Must Have** *(Imprescindible)* | • Configuración de Django sin base de datos (`DATABASES = {}` en `miproyecto/settings.py`) [cite: 2].<br>• Ingesta y lectura directa de `datos.json` [cite: 2].<br>• Lógica de sanitización y motor RAG TF-IDF en memoria dentro de `solucion.py` [cite: 2].<br>• Cliente de inferencia HTTP con timeout para Ollama (`llama3`) con fallback en `solucion.py` [cite: 2].<br>• Endpoints y vistas en `core/views.py` para procesar payloads JSON [cite: 2].<br>• Template `core/templates/resumen.html` para previsualización de resultados. |
| **Should Have** *(Importante)* | • Endpoint/acción en `core/views.py` para recargar `datos.json` en caliente sin reiniciar el servidor.<br>• Reporte de tiempos de ejecución (`execution_time_ms`) e IDs coincidentes (`matched_history_ids`) [cite: 2].<br>• Suite de tests en `core/tests.py` para validar sanitización, RAG y vistas [cite: 2]. |
| **Could Have** *(Deseable)* | • Contenedorización lista para producción mediante `Dockerfile` y `docker-compose.yml`.<br>• Variables de entorno parametrizadas vía `.env` y documentadas en `.env.example`. |
| **Won't Have** *(Fuera de alcance)* | • Migraciones o persistencia en PostgreSQL, MySQL o SQLite (`core/models.py` queda vacío/sin ORM) [cite: 2].<br>• Dependencia de APIs cloud de terceros (OpenAI, Anthropic) [cite: 2]. |

---

## 5. Especificación OpenSpec v1.0 Adaptada a la Estructura de Archivos

```yaml
# ==============================================================================
# OPENSPEC SPECIFICATION (rag-mail-triage)
# ==============================================================================
spec_version: "1.0"
project:
  name: "rag-mail-triage"
  version: "1.0.0"
  runtime: "Python >= 3.11 / Django >= 5.0"
  architecture: "Django Project (miproyecto/) + App (core/) + Engine (solucion.py) + Dataset (datos.json)"

# ------------------------------------------------------------------------------
# A. DATOS DE ENTRADA (DATA CONTRACTS)
# ------------------------------------------------------------------------------
data_inputs:
  EmailPayloadJSON:
    type: "object"
    required: ["message_id", "from", "subject", "body"]
    properties:
      message_id:
        type: "string"
        description: "Identificador único del correo (RFC o UUID)."
        example: "MSG-2026-0824-001"
      from:
        type: "string"
        format: "email"
        description: "Correo del remitente."
        example: "proveedor@empresa.com"
      subject:
        type: "string"
        description: "Asunto del mensaje."
        example: "Alerta de vencimiento de servicio crítico"
      body:
        type: "string"
        description: "Cuerpo del correo (texto plano o HTML con firmas/citas)."

  RootDatasetJSON:
    file_path: "datos.json"
    type: "array"
    items:
      type: "object"
      required: ["id", "from", "subject", "body", "priority_score", "category"]
      properties:
        id: { type: "string" }
        from: { type: "string" }
        subject: { type: "string" }
        body: { type: "string" }
        priority_score: { type: "integer", minimum: 1, maximum: 5 }
        category: { type: "string" }

# ------------------------------------------------------------------------------
# B. REGLAS (IMPLEMENTADAS EN solucion.py)
# ------------------------------------------------------------------------------
rules:
  sanitization:
    - id: "RULE-SAN-01"
      name: "Strip Quotes & Signatures"
      pattern: "(?m)^>.*$|(?i)(el \d+.*escribió:|on .* wrote:).*"
      file: "solucion.py -> clean_email_body()"
    - id: "RULE-SAN-02"
      name: "Strip Disclaimers"
      pattern: "(?i)(este mensaje y sus archivos adjuntos son confidenciales|this email is confidential).*$"
      file: "solucion.py -> clean_email_body()"

  rag_retrieval:
    - id: "RULE-RAG-01"
      name: "In-Memory TF-IDF Similarity"
      corpus_file: "datos.json"
      file: "solucion.py -> JSONRagEngine"
      description: "Recupera Top-2 casos similares con umbral de similitud coseno > 0.05."

  classification_and_fallback:
    - id: "RULE-CLS-01"
      name: "LLM Structured JSON Schema"
      model: "llama3"
      file: "solucion.py -> analyze_email()"
    - id: "RULE-CLS-02"
      name: "Timeout & Deterministic Fallback"
      threshold_seconds: 2.5
      fallback_logic: |
        Si detecta ['vence', 'suspenderá', 'corte', 'error 500', 'urgente']:
          priority = 5, category = 'Ticket Crítico', suggested_action = 'Atención inmediata.'
        De lo contrario:
          priority = 2, category = 'Informativo', suggested_action = 'Archivar o leer al final del día.'

# ------------------------------------------------------------------------------
# C. PAQUETES EXTERNOS (requirements.txt)
# ------------------------------------------------------------------------------
external_packages:
  - "django>=5.0.0"
  - "djangorestframework>=3.15.0"
  - "scikit-learn>=1.4.0"
  - "numpy>=1.26.0"
  - "requests>=2.31.0"
  - "pydantic>=2.6.0"
  - "python-dotenv>=1.0.0"

# ------------------------------------------------------------------------------
# D. VISTAS (core/views.py & core/templates/resumen.html)
# ------------------------------------------------------------------------------
endpoints:
  - path: "/api/classify/"
    view: "core.views.ClassifyEmailView"
    method: "POST"
    description: "Recibe EmailPayloadJSON, ejecuta solucion.py y responde JSON con TriageResponse."

  - path: "/resumen/"
    view: "core.views.ResumenTemplateView"
    method: "GET"
    description: "Renderiza core/templates/resumen.html para visualización amigable de correos procesados."

  - path: "/api/reload/"
    view: "core.views.ReloadCorpusView"
    method: "POST"
    description: "Invoca la recarga en caliente de datos.json en solucion.py."
```

---

## 6. Mapeo de Responsabilidades en la Estructura de Archivos

```text
rag-mail-triage/
├── core/
│   ├── templates/
│   │   └── resumen.html           # Vista HTML de resultados y dashboard básico
│   ├── admin.py                   # Registro admin (vacío/no-op)
│   ├── apps.py                    # Inicialización del motor RAG de solucion.py al arrancar Django
│   ├── models.py                  # Vacío (sin modelos ORM)
│   ├── tests.py                   # Pruebas unitarias para solucion.py y views.py
│   └── views.py                   # Endpoints de API y renderizado del template resumen.html
├── docs/
│   ├── arquitectura.md            # Diagramas y flujo de datos
│   ├── openspec.md                # Especificación técnica formal
│   └── roadmap.md                 # Fases de iteración del proyecto
├── miproyecto/
│   ├── settings.py                # Configuración sin BD (DATABASES = {})
│   ├── urls.py                    # Enrutamiento hacia core/views.py
│   └── wsgi.py
├── .env / .env.example            # Variables de configuración (Host Ollama, puertos)
├── datos.json                     # Dataset histórico de referencia para RAG
├── docker-compose.yml / Dockerfile # Configuración de despliegue en contenedor
├── ia.md                          # Instrucciones y contexto para agentes de IA
├── manage.py                      # CLI de Django
├── plan.md                        # Este documento de especificación y arquitectura
├── README.md                      # Documentación de inicio rápido
├── requirements.txt               # Lista de dependencias de Python
└── solucion.py                    # Pipeline central: Sanitizador, RAG en memoria (datos.json) y LLM Fallback
# RAG Mail Triage

Microservicio Django local para clasificar correos usando el historial de `datos.json`. El sistema valida y sanitiza cada mensaje, recupera casos similares mediante TF-IDF y consulta un modelo local de Ollama. Si Ollama no está disponible, aplica un fallback heurístico determinista.

## Flujo

```text
correo JSON -> validación -> sanitización -> RAG TF-IDF -> Ollama/fallback
    -> clasificación -> persistencia en datos.json -> actualización del índice
```

No utiliza base de datos relacional ni ORM. Cada correo válido se guarda con su clasificación. No se duplican mensajes con el mismo `message_id` ni con el mismo remitente, asunto y cuerpo.

## Requisitos

- Python 3.11 o superior
- Docker Engine y Docker Compose, si se usa el contenedor
- Ollama opcional para clasificación LLM local

## Ejecutar en local

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python manage.py runserver 127.0.0.1:8000
```

En este equipo, como alternativa temporal, las dependencias pueden instalarse con `python3 -m pip install --break-system-packages -r requirements.txt`.

## Ejecutar con Docker

```bash
docker compose up --build
```

El servicio queda disponible en el puerto definido por `APP_PORT` (por defecto, `8000`). La configuración actual mantiene el contenedor activo para permitir ejecutar el servidor Django manualmente.

## Configuración

Copiar `.env.example` a `.env` y ajustar, cuando sea necesario:

- `OLLAMA_HOST`: URL del servicio Ollama.
- `OLLAMA_MODEL`: modelo preferido, por defecto `llama3`.
- `OLLAMA_TIMEOUT_SECONDS`: tiempo máximo de inferencia, por defecto `60`.
- `APP_PORT`: puerto local publicado por Docker Compose.

No versionar `.env` ni credenciales.

## Probar la API

```bash
curl -X POST http://127.0.0.1:8000/api/classify/ \
	-H 'Content-Type: application/json' \
	-d '{"message_id":"MSG-LOCAL-001","from":"alertas@empresa.com","subject":"Corte urgente","body":"El servicio presenta error 500."}'
```

Payload requerido: `message_id`, `from`, `subject` y `body`. La respuesta incluye `summary`, `priority`, `category`, `suggested_action`, `matched_history_ids`, `fallback_used` y `execution_time_ms`.

## Endpoints

- `POST /api/classify/`: clasifica y persiste un correo válido.
- `POST /api/reload/`: recarga `datos.json` en memoria.
- `GET /resumen/`: muestra la vista web de resumen.

## Estructura

- `solucion.py`: sanitización, recuperación TF-IDF, Ollama y fallback.
- `core/views.py`: API, persistencia y recarga del corpus.
- `datos.json`: historial utilizado como corpus RAG.
- `docs/`: arquitectura, especificación y roadmap.
- `core/tests.py`: pruebas de lógica y endpoints.

## Limitaciones actuales

- El corpus se mantiene en memoria y se persiste en un único archivo JSON.
- La búsqueda semántica actual usa TF-IDF, no embeddings.
- Docker Compose no levanta Ollama automáticamente.
- `DEBUG` está habilitado para desarrollo local; no es una configuración de producción.

# OpenSpec - RAG Mail Triage

## Estado actual

Implementado como microservicio Django local, sin base de datos relacional. La especificación debe leerse junto con `solucion.py`, `core/views.py` y `README.md`.

## Problema

Sobrecarga administrativa provocada por correos electrónicos.

## Entrada

El endpoint `POST /api/classify/` recibe un objeto JSON con estos campos obligatorios:

- `message_id`: identificador del correo.
- `from`: remitente con formato básico de correo.
- `subject`: asunto.
- `body`: cuerpo no vacío.

## Salida

La respuesta incluye:

- `message_id`
- `summary`
- `priority` de `1` a `5`
- `category`: `Ticket crítico`, `Requiere firma`, `Informativo` o `Dato inválido`
- `suggested_action`
- `matched_history_ids`
- `fallback_used`
- `execution_time_ms`

Los correos válidos se persisten en `datos.json`. Se evita la duplicación por `message_id` o por contenido.

## Reglas técnicas

- La recuperación usa TF-IDF y similitud de coseno con umbral mayor que `0.05`.
- Se recuperan como máximo dos casos históricos.
- Ollama se consulta en `OLLAMA_HOST` con el modelo configurado en `OLLAMA_MODEL`.
- El timeout se controla con `OLLAMA_TIMEOUT_SECONDS`, cuyo valor predeterminado es `60` segundos.
- Si Ollama no responde o devuelve una categoría inválida, se aplica el fallback heurístico.

## Endpoints

- `POST /api/classify/`
- `POST /api/reload/`
- `GET /resumen/`

## Objetivo

Clasificar correos y priorizarlos.
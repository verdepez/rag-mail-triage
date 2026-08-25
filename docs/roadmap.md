# Roadmap

## EVA1: base local - completada
 Python y entorno virtual
 JSON como persistencia local
 Django y endpoint web
 Pruebas de lógica y API
- Pruebas de lógica y API

 Dockerfile y Docker Compose
 RAG local con TF-IDF sobre `datos.json`
 Ollama opcional con detección automática del modelo
 Fallback heurístico cuando Ollama no está disponible
 Persistencia y deduplicación de correos clasificados
 Recarga del corpus sin reiniciar Django
- RAG local con TF-IDF sobre `datos.json`
- Ollama opcional con detección automática del modelo
 Definir un flujo estable de arranque conjunto para Django y Ollama.
 Separar corpus de prueba y corpus operativo.
 Medir precisión, latencia y tasa de uso del fallback.
- Fallback heurístico cuando Ollama no está disponible
- Persistencia y deduplicación de correos clasificados
 Embeddings y Qdrant.
 Flujo de ingesta desde la carpeta `Cerebro/`.
 FastAPI, si aporta una separación clara del servicio.
 OpenTelemetry para métricas y trazas.
 Swagger/OpenAPI publicado y validado.
 Evaluación de modelos y prompts versionados.

- Definir un flujo estable de arranque conjunto para Django y Ollama.
- Separar corpus de prueba y corpus operativo.
- Medir precisión, latencia y tasa de uso del fallback.

## EVA3: evolución - futura

- Embeddings y Qdrant.
- Flujo de ingesta desde la carpeta `Cerebro/`.
- FastAPI, si aporta una separación clara del servicio.
- OpenTelemetry para métricas y trazas.
- Swagger/OpenAPI publicado y validado.
- Evaluación de modelos y prompts versionados.

## Criterio de avance

Cada fase se considera avanzada cuando existe implementación verificable, documentación actualizada y pruebas reproducibles en local.
``
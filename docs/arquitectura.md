# Arquitectura ES1

## Componentes

- `core/views.py`: expone la API, coordina el análisis y persiste resultados.
- `solucion.py`: contiene validación, sanitización, recuperación TF-IDF, cliente Ollama y fallback.
- `datos.json`: corpus histórico y persistencia local de correos clasificados.
- `miproyecto/`: configuración y rutas Django.
- `core/templates/resumen.html`: vista web de resultados.

## Flujo de datos

```text
Cliente
	|
	v
POST /api/classify/
	|
	v
Validación del payload
	|
	v
Sanitización del correo
	|
	v
TF-IDF sobre datos.json en memoria
	|
	+--> Ollama: modelo generativo disponible
	|        |
	|        +--> fallback heurístico si falla
	v
Resultado de triage
	|
	v
Deduplicación y persistencia en datos.json
	|
	v
Reconstrucción del índice RAG
```

## Decisiones actuales

- No se utiliza base de datos relacional ni ORM.
- La búsqueda RAG es local, en memoria y basada en TF-IDF.
- Ollama es opcional: el servicio sigue funcionando con fallback.
- El modelo se detecta mediante `/api/tags`; se excluyen modelos de embeddings.
- La persistencia usa escritura temporal y reemplazo atómico del JSON.

## Endpoints

- `POST /api/classify/`: valida, clasifica y persiste un correo.
- `POST /api/reload/`: reconstruye el índice desde `datos.json`.
- `GET /resumen/`: renderiza el resumen web.

## Evolución prevista

```text
TF-IDF local -> embeddings -> Qdrant
Ollama local -> modelos y prompts versionados
JSON local -> almacenamiento estructurado cuando el volumen lo justifique
```
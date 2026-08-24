 # RAG Mail Triage

Microservicio Django local para clasificar correos con contexto histórico de `datos.json`. No utiliza base de datos ni requiere Ollama: si Ollama no está disponible, aplica el fallback heurístico.

Cada correo válido enviado a `POST /api/classify/` queda guardado en `datos.json` con su clasificación. Si se repite el mismo `message_id` o el mismo contenido, no se duplica. El cliente detecta automáticamente los modelos instalados en Ollama; configura `OLLAMA_TIMEOUT_SECONDS` en `.env` si el primer arranque del modelo tarda más.

## Ejecutar en local

Con `python3-venv` instalado:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python manage.py runserver 127.0.0.1:8000
```

En este equipo, como alternativa temporal, las dependencias pueden instalarse con `python3 -m pip install --break-system-packages -r requirements.txt`.

## Probar la API

```bash
curl -X POST http://127.0.0.1:8000/api/classify/ \
	-H 'Content-Type: application/json' \
	-d '{"message_id":"MSG-LOCAL-001","from":"alertas@empresa.com","subject":"Corte urgente","body":"El servicio presenta error 500."}'
```

Endpoints disponibles:

- `POST /api/classify/`
- `POST /api/reload/`
- `GET /resumen/`

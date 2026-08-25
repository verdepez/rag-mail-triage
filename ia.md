
# Contexto para IA: RAG Mail Triage

## Propósito

Clasificar correos administrativos y operativos según urgencia, categoría y acción recomendada, usando casos históricos propios como contexto. El proyecto es local y prioriza privacidad, trazabilidad y continuidad cuando el modelo no está disponible.

## Flujo de procesamiento

1. `core/views.py` recibe un objeto JSON mediante `POST /api/classify/`.
2. `solucion.py` valida `message_id`, `from`, `subject` y `body`.
3. `clean_email_body()` elimina citas, firmas y disclaimers comunes.
4. `JSONRagEngine` busca hasta dos casos similares en `datos.json` con TF-IDF y similitud de coseno mayor que `0.05`.
5. Se consulta el modelo generativo disponible en Ollama, prefiriendo `OLLAMA_MODEL` o `llama3`.
6. Si Ollama falla, se usa una clasificación heurística determinista.
7. El resultado válido se guarda en `datos.json` y el índice se reconstruye.

## Categorías

- `Ticket crítico`: urgencias, caídas, cortes, errores 500 o bloqueos operativos. Prioridad esperada: `5`.
- `Requiere firma`: contratos, convenios, autorizaciones o visados. Prioridad esperada: `4`.
- `Informativo`: avisos generales, boletines o contenido sin acción urgente. Prioridad esperada: `1` o `2`.
- `Dato inválido`: payload incompleto, remitente inválido o cuerpo vacío. Prioridad: `1`.

## Contrato de respuesta

El analizador devuelve `message_id`, `summary`, `priority`, `category`, `suggested_action`, `matched_history_ids`, `fallback_used` y `execution_time_ms`.

## Criterios para futuras mejoras

- Mantener el procesamiento local y no enviar correos a servicios cloud sin una decisión explícita.
- Separar datos de prueba, datos reales y secretos.
- Medir precisión por categoría y revisar falsos positivos del fallback.
- Migrar de TF-IDF a embeddings y Qdrant cuando el corpus y el flujo de ingesta estén preparados.
- Conservar en Markdown las decisiones, resultados de pruebas y aprendizajes del proyecto.

import json
import os
import re
import time
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Estados válidos permitidos por el sistema
ALLOWED_CATEGORIES = [
    "Dato inválido",
    "Ticket crítico",
    "Requiere firma",
    "Informativo",
]
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_TIMEOUT_SECONDS = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "60"))


def select_ollama_model(preferred_model: str = "llama3") -> str | None:
    """Devuelve el modelo generativo disponible más adecuado en Ollama."""
    try:
        response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=0.5)
        if response.status_code != 200:
            return None
        models = [item.get("name", "") for item in response.json().get("models", [])]
    except (requests.RequestException, ValueError, TypeError):
        return None

    generative_models = [
        model for model in models
        if model and "embed" not in model.lower()
    ]
    if preferred_model in generative_models:
        return preferred_model
    preferred_base = preferred_model.split(":", 1)[0]
    for model in generative_models:
        if model.split(":", 1)[0] == preferred_base:
            return model
    return generative_models[0] if generative_models else None


# ==========================================
# 1. PIPELINE DE VALIDACIÓN Y SANITIZACIÓN
# ==========================================
def validate_email_payload(email_data: dict) -> tuple[bool, str]:
    """Valida que el payload entrante contenga los campos requeridos y tipos correctos."""
    required_keys = ["message_id", "from", "subject", "body"]
    for key in required_keys:
        if key not in email_data:
            return False, f"Falta el campo obligatorio: '{key}'"
        if not isinstance(email_data[key], str):
            return False, f"El campo '{key}' debe ser de tipo texto (string)"

    # Validación básica de contenido no vacío
    if (
        not email_data["from"].strip()
        or "@" not in email_data["from"]
        or not email_data["body"].strip()
    ):
        return (
            False,
            "Formato de remitente ('from') inválido o cuerpo ('body') vacío",
        )

    return True, "OK"


def clean_email_body(raw_text: str) -> str:
    """Elimina disclaimers legales, firmas y cadenas de respuesta anidadas."""
    # Eliminar bloques de respuesta y citas
    text = re.sub(r"(?m)^>.*$", "", raw_text)
    text = re.sub(r"(?i)(el \d+.*escribió:|on .* wrote:).*", "", text)

    # Eliminar disclaimers legales típicos
    text = re.sub(
        r"(?i)(este mensaje y sus archivos adjuntos son confidenciales|this email is confidential).*$",
        "",
        text,
    )

    # Normalizar espacios en blanco
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ==========================================
# 2. MOTOR RAG EN MEMORIA (TF-IDF + datos.json)
# ==========================================
class JSONRagEngine:

    def __init__(self, json_filepath: str = "datos.json"):
        self.json_filepath = json_filepath
        self.history_data = self._load_data()
        self.vectorizer = TfidfVectorizer(stop_words=None)
        self.tfidf_matrix = None
        self._fit()

    def _load_data(self) -> list:
        if not os.path.exists(self.json_filepath):
            return []
        with open(self.json_filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def _fit(self):
        if self.history_data:
            corpus = [
                f"{d.get('subject', '')} {d.get('body', '')}"
                for d in self.history_data
            ]
            self.tfidf_matrix = self.vectorizer.fit_transform(corpus)

    def retrieve_similar(self, query_text: str, top_k: int = 2) -> list:
        if not self.history_data or self.tfidf_matrix is None:
            return []

        query_vec = self.vectorizer.transform([query_text])
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        top_indices = similarities.argsort()[-top_k:][::-1]

        results = []
        for idx in top_indices:
            if similarities[idx] > 0.05:  # Umbral mínimo de correlación
                item = self.history_data[idx].copy()
                item["similarity_score"] = round(float(similarities[idx]), 3)
                results.append(item)
        return results


# ==========================================
# 3. ANALIZADOR DE TRIAGE (LLM + FALLBACK)
# ==========================================
def analyze_email(
    email: dict, rag_engine: JSONRagEngine, ollama_model: str | None = None
) -> dict:
    start_time = time.time()
    ollama_model = ollama_model or os.getenv("OLLAMA_MODEL", "llama3")

    # 1. Validación de esquema y datos
    is_valid, validation_error = validate_email_payload(email)
    if not is_valid:
        return {
            "message_id": email.get("message_id", "UNKNOWN"),
            "summary": f"Error de validación: {validation_error}",
            "priority": 1,
            "category": "Dato inválido",
            "suggested_action": "Descartar correo o notificar error en payload.",
            "matched_history_ids": [],
            "fallback_used": True,
            "execution_time_ms": round((time.time() - start_time) * 1000, 2),
        }

    # 2. Sanitización
    cleaned_body = clean_email_body(email["body"])
    query_text = f"{email['subject']} {cleaned_body}"

    # 3. Búsqueda RAG
    similar_cases = rag_engine.retrieve_similar(query_text, top_k=2)
    matched_ids = [c["id"] for c in similar_cases]
    context_str = json.dumps(similar_cases, ensure_ascii=False, indent=2)

    # 4. Inferencia con LLM (Ollama)
    prompt = f"""
Eres un asistente de triage de correo para personal administrativo.
Clasifica el correo entrante apoyándote en los casos históricos recuperados.

CASOS HISTÓRICOS:
{context_str}

CORREO ENTRANTE:
De: {email['from']}
Asunto: {email['subject']}
Cuerpo: {cleaned_body}

REGLAS DE CATEGORIZACIÓN:
Debes elegir EXCLUSIVAMENTE una de las siguientes categorías para "category":
- "Ticket crítico" (Urgencias, caídas de servicio, fallos 500, bloqueos operativos) -> priority 5
- "Requiere firma" (Contratos, convenios, autorizaciones formales, visados) -> priority 4
- "Informativo" (Boletines, encuestas, noticias, avisos generales) -> priority 1 o 2

Responde ÚNICAMENTE un JSON válido con las siguientes claves:
{{
  "summary": "Resumen ejecutivo en 1 o 2 líneas",
  "priority": 1 a 5,
  "category": "Ticket crítico" | "Requiere firma" | "Informativo",
  "suggested_action": "Acción inmediata recomendada"
}}
"""

    try:
        available_model = select_ollama_model(ollama_model)
        if not available_model:
            raise requests.RequestException("No hay un modelo generativo disponible")
        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": available_model,
                "prompt": prompt,
                "stream": False,
                "format": "json",
            },
            timeout=OLLAMA_TIMEOUT_SECONDS,
        )
        if response.status_code == 200:
            parsed = json.loads(response.json().get("response", "{}"))
            if parsed.get("category") in ALLOWED_CATEGORIES:
                parsed["message_id"] = email["message_id"]
                parsed["matched_history_ids"] = matched_ids
                parsed["fallback_used"] = False
                parsed["execution_time_ms"] = round(
                    (time.time() - start_time) * 1000, 2
                )
                return parsed
    except Exception:
        pass

    # 5. Fallback Heurístico (en caso de timeout o ausencia de Ollama)
    text_to_eval = f"{email['subject']} {cleaned_body}".lower()

    if any(
        w in text_to_eval
        for w in [
            "vence",
            "suspenderá",
            "error 500",
            "urgente",
            "corte",
            "caída",
        ]
    ):
        priority, category, action = (
            5,
            "Ticket crítico",
            "Escalar a jefatura y resolver de inmediato.",
        )
    elif any(
        w in text_to_eval
        for w in ["firma", "convenio", "contrato", "visado", "autorización"]
    ):
        priority, category, action = (
            4,
            "Requiere firma",
            "Revisar documento legal y gestionar firma electrónica.",
        )
    else:
        priority, category, action = (
            2,
            "Informativo",
            "Archivar o revisar al cierre de la jornada.",
        )

    return {
        "message_id": email["message_id"],
        "summary": f"Procesamiento sobre: {email['subject']}",
        "priority": priority,
        "category": category,
        "suggested_action": action,
        "matched_history_ids": matched_ids,
        "fallback_used": True,
        "execution_time_ms": round((time.time() - start_time) * 1000, 2),
    }


# ==========================================
# 4. EJECUCIÓN DE PRUEBAS (DEMO DE ESTADOS)
# ==========================================
if __name__ == "__main__":
    print("=== INICIALIZANDO MOTOR RAG LOCAL (datos.json) ===\n")
    engine = JSONRagEngine("datos.json")

    casos_de_prueba = [
        # Caso 1: Ticket crítico
        {
            "message_id": "TEST-001",
            "from": "alertas@cloud.com",
            "subject": "ALERTA: Corte inminente de base de datos",
            "body": "Estimados, el servicio de base de datos presenta error 500 y vencerá el plazo de pago hoy a las 17:00.",
        },
        # Caso 2: Requiere firma
        {
            "message_id": "TEST-002",
            "from": "notaria@legal.cl",
            "subject": "Contrato de arrendamiento listo para visado",
            "body": "Adjuntamos el convenio final. Solicitamos la firma del representante legal para cerrar el trámite.",
        },
        # Caso 3: Informativo
        {
            "message_id": "TEST-003",
            "from": "comunicaciones@empresa.com",
            "subject": "Menú semanal de la cafetería",
            "body": "Hola a todos, les compartimos las opciones de almuerzo disponibles para esta semana.",
        },
        # Caso 4: Dato inválido
        {
            "message_id": "TEST-004",
            "from": "invalido-sin-arroba",
            "subject": "Test Payload Erróneo",
            "body": "",
        },
    ]

    for caso in casos_de_prueba:
        print(
            f"--> Procesando mensaje: {caso.get('message_id')} ('{caso.get('subject')}')"
        )
        resultado = analyze_email(caso, engine)
        print(json.dumps(resultado, ensure_ascii=False, indent=2))
        print("-" * 60)
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from solucion import JSONRagEngine, analyze_email


DATASET_PATH = Path(__file__).resolve().parent.parent / "datos.json"
rag_engine = JSONRagEngine(str(DATASET_PATH))


def _content_key(email):
	return tuple(email[field].strip().casefold() for field in ("from", "subject", "body"))


def _save_classified_email(email, result):
	record = {
		"id": email["message_id"],
		"from": email["from"],
		"subject": email["subject"],
		"body": email["body"],
		"priority_score": result["priority"],
		"category": result["category"],
		"summary": result["summary"],
		"suggested_action": result["suggested_action"],
	}

	with DATASET_PATH.open("r", encoding="utf-8") as dataset_file:
		records = json.load(dataset_file)
	records = [item for item in records if item.get("id") != record["id"]]
	unique_records = []
	seen_content = set()
	for item in records:
		item_key = _content_key(item)
		if item_key not in seen_content:
			seen_content.add(item_key)
			unique_records.append(item)
	if _content_key(record) not in seen_content:
		unique_records.append(record)

	if unique_records == records:
		return False

	with NamedTemporaryFile(
		"w", encoding="utf-8", dir=DATASET_PATH.parent, delete=False
	) as temporary_file:
		json.dump(unique_records, temporary_file, ensure_ascii=False, indent=2)
		temporary_file.write("\n")
		temporary_path = temporary_file.name
	os.replace(temporary_path, DATASET_PATH)
	return True


def _refresh_engine():
	global rag_engine
	rag_engine = JSONRagEngine(str(DATASET_PATH))


@csrf_exempt
def classify_email(request):
	if request.method != "POST":
		return JsonResponse({"error": "Usa el método POST."}, status=405)
	try:
		payload = json.loads(request.body)
	except json.JSONDecodeError:
		return JsonResponse({"error": "El cuerpo debe ser JSON válido."}, status=400)
	if not isinstance(payload, dict):
		return JsonResponse({"error": "El payload debe ser un objeto JSON."}, status=400)
	result = analyze_email(payload, rag_engine)
	if result["category"] != "Dato inválido":
		if _save_classified_email(payload, result):
			_refresh_engine()
	return JsonResponse(result)


@csrf_exempt
def reload_corpus(request):
	if request.method != "POST":
		return JsonResponse({"error": "Usa el método POST."}, status=405)
	_refresh_engine()
	return JsonResponse({"status": "ok", "records_loaded": len(rag_engine.history_data)})


def resumen(request):
	return render(request, "resumen.html")


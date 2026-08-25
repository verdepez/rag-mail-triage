import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from django.test import Client, SimpleTestCase

from core import views
from solucion import JSONRagEngine, analyze_email, clean_email_body, select_ollama_model


class TriageTests(SimpleTestCase):
	def setUp(self):
		self.client = Client()
		self.engine = JSONRagEngine()
		self.email = {
			"message_id": "TEST-001",
			"from": "alertas@empresa.com",
			"subject": "Alerta de corte urgente",
			"body": "El servicio presenta error 500.\n\nEste mensaje y sus archivos adjuntos son confidenciales.",
		}

	def test_clean_email_body_removes_quotes_and_disclaimer(self):
		cleaned = clean_email_body(self.email["body"] + "\n> mensaje anterior")

		self.assertEqual(cleaned, "El servicio presenta error 500.")

	def test_analyze_email_uses_critical_fallback(self):
		with patch("solucion.requests.get", side_effect=Exception("Ollama offline")), patch(
			"solucion.requests.post", side_effect=Exception("Ollama offline")
		):
			result = analyze_email(self.email, self.engine)

		self.assertTrue(result["fallback_used"])
		self.assertEqual(result["priority"], 5)
		self.assertEqual(result["category"], "Ticket crítico")

	def test_selects_available_generative_model(self):
		response = type("Response", (), {
			"status_code": 200,
			"json": lambda self: {"models": [
				{"name": "nomic-embed-text:latest"},
				{"name": "qwen2.5:3b"},
			]},
		})()
		with patch("solucion.requests.get", return_value=response):
			model = select_ollama_model("llama3")

		self.assertEqual(model, "qwen2.5:3b")

	def test_classify_endpoint_returns_json(self):
		with tempfile.TemporaryDirectory() as temporary_directory:
			dataset_path = Path(temporary_directory) / "datos.json"
			dataset_path.write_text("[]", encoding="utf-8")
			with patch.object(views, "DATASET_PATH", dataset_path), patch.object(
				views, "rag_engine", JSONRagEngine(str(dataset_path))
			), patch("solucion.requests.get", side_effect=Exception("Ollama offline")), patch(
				"solucion.requests.post", side_effect=Exception("Ollama offline")
			):
				response = self.client.post(
					"/api/classify/", data=self.email, content_type="application/json"
				)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.json()["message_id"], "TEST-001")

	def test_resumen_classifies_with_django_post(self):
		with tempfile.TemporaryDirectory() as temporary_directory:
			dataset_path = Path(temporary_directory) / "datos.json"
			dataset_path.write_text("[]", encoding="utf-8")
			with patch.object(views, "DATASET_PATH", dataset_path), patch.object(
				views, "rag_engine", JSONRagEngine(str(dataset_path))
			), patch("solucion.requests.get", side_effect=Exception("Ollama offline")), patch(
				"solucion.requests.post", side_effect=Exception("Ollama offline")
			):
				response = self.client.post(
					"/resumen/",
					data={
						"from": self.email["from"],
						"subject": self.email["subject"],
						"body": self.email["body"],
					},
				)

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Ticket crítico")

	def test_classify_endpoint_persists_email_in_dataset(self):
		with tempfile.TemporaryDirectory() as temporary_directory:
			dataset_path = Path(temporary_directory) / "datos.json"
			dataset_path.write_text("[]", encoding="utf-8")
			with patch.object(views, "DATASET_PATH", dataset_path), patch.object(
				views, "rag_engine", JSONRagEngine(str(dataset_path))
			), patch("solucion.requests.get", side_effect=Exception("Ollama offline")), patch(
				"solucion.requests.post", side_effect=Exception("Ollama offline")
			):
				response = self.client.post(
					"/api/classify/", data=self.email, content_type="application/json"
				)

			saved_records = json.loads(dataset_path.read_text(encoding="utf-8"))

		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(saved_records), 1)
		self.assertEqual(saved_records[0]["id"], "TEST-001")
		self.assertEqual(saved_records[0]["category"], "Ticket crítico")

	def test_classify_endpoint_does_not_duplicate_same_content(self):
		with tempfile.TemporaryDirectory() as temporary_directory:
			dataset_path = Path(temporary_directory) / "datos.json"
			dataset_path.write_text(json.dumps([{
				"id": "OLD-001",
				"from": self.email["from"],
				"subject": self.email["subject"],
				"body": self.email["body"],
				"priority_score": 5,
				"category": "Ticket crítico",
			}]), encoding="utf-8")
			with patch.object(views, "DATASET_PATH", dataset_path), patch.object(
				views, "rag_engine", JSONRagEngine(str(dataset_path))
			), patch("solucion.requests.post", side_effect=Exception("Ollama offline")):
				response = self.client.post(
					"/api/classify/", data={**self.email, "message_id": "NEW-001"}, content_type="application/json"
				)

			saved_records = json.loads(dataset_path.read_text(encoding="utf-8"))

		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(saved_records), 1)
		self.assertEqual(saved_records[0]["id"], "OLD-001")

	def test_invalid_json_returns_bad_request(self):
		response = self.client.post("/api/classify/", data="not-json", content_type="application/json")

		self.assertEqual(response.status_code, 400)

	def test_reload_endpoint_reports_dataset_size(self):
		response = self.client.post("/api/reload/")
		expected_records = len(json.loads(views.DATASET_PATH.read_text(encoding="utf-8")))

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.json()["records_loaded"], expected_records)

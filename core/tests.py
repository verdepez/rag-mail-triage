from unittest.mock import patch

from django.contrib.auth.models import Group, User
from django.test import Client, TestCase

from core.models import Registro
from solucion import JSONRagEngine, analyze_email, clean_email_body, decidir, select_ollama_model


class SolucionUnitTests(TestCase):
    def setUp(self):
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
        with patch("solucion.requests.get", side_effect=Exception("offline")), patch(
            "solucion.requests.post", side_effect=Exception("offline")
        ):
            result = analyze_email(self.email, self.engine)

        self.assertTrue(result["fallback_used"])
        self.assertEqual(result["priority"], 5)
        self.assertEqual(result["category"], "Ticket crítico")

    def test_decidir_function_returns_category(self):
        with patch("solucion.requests.get", side_effect=Exception("offline")), patch(
            "solucion.requests.post", side_effect=Exception("offline")
        ):
            cat_critico = decidir("Error 500 en el servidor", "El sistema se cayó", "alertas@cloud.com")
            cat_firma = decidir("Convenio de visado", "Requiere la firma del gerente", "legal@empresa.com")
            cat_info = decidir("Menú semanal", "Opciones del casino", "casino@empresa.com")
            cat_inv = decidir("", "")

        self.assertEqual(cat_critico, "Ticket crítico")
        self.assertEqual(cat_firma, "Requiere firma")
        self.assertEqual(cat_info, "Informativo")
        self.assertEqual(cat_inv, "Dato inválido")


class RegistroModelTests(TestCase):
    def test_registro_creation_and_soft_delete(self):
        reg = Registro.objects.create(
            remitente="contacto@cliente.com",
            asunto="Solicitud de contrato",
            cuerpo="Favor firmar el documento",
            prioridad=4,
            categoria="Requiere firma",
        )
        self.assertFalse(reg.eliminado)
        self.assertIsNone(reg.fecha_eliminacion)
        self.assertEqual(Registro.objects.filter(eliminado=False).count(), 1)

        # Probar soft_delete
        reg.soft_delete()
        self.assertTrue(reg.eliminado)
        self.assertIsNotNone(reg.fecha_eliminacion)
        self.assertEqual(Registro.objects.filter(eliminado=False).count(), 0)

    def test_registro_compatibility_properties(self):
        reg = Registro(remitente="test@user.com", prioridad=3, categoria="Informativo")
        self.assertEqual(reg.nombre, "test@user.com")
        self.assertEqual(reg.cantidad, 3)
        self.assertEqual(reg.estado, "Informativo")
        self.assertEqual(reg.resultado, "Informativo")


class CrudAndAuthTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Crear grupos
        self.grp_admin, _ = Group.objects.get_or_create(name="admin")
        self.grp_normal, _ = Group.objects.get_or_create(name="normal")
        self.grp_viewer, _ = Group.objects.get_or_create(name="viewer")

        # Crear usuarios
        self.user_admin = User.objects.create_user("admin_user", password="password123")
        self.user_admin.groups.add(self.grp_admin)

        self.user_normal = User.objects.create_user("normal_user", password="password123")
        self.user_normal.groups.add(self.grp_normal)

        self.user_viewer = User.objects.create_user("viewer_user", password="password123")
        self.user_viewer.groups.add(self.grp_viewer)

        # Registro de prueba
        self.reg = Registro.objects.create(
            remitente="antiguo@empresa.com",
            asunto="Aviso general",
            cuerpo="Texto informativo",
            prioridad=2,
            categoria="Informativo",
        )

    def test_unauthenticated_user_redirected_to_login(self):
        response = self.client.get("/registros/")
        self.assertRedirects(response, "/login/?next=/registros/")

    def test_viewer_can_view_list_but_cannot_create_or_edit(self):
        self.client.login(username="viewer_user", password="password123")

        # Lista: acceso permitido
        res_list = self.client.get("/registros/")
        self.assertEqual(res_list.status_code, 200)

        # Crear: denegado por servidor (redirección a lista con mensaje de error)
        res_crear = self.client.get("/registros/crear/")
        self.assertRedirects(res_crear, "/registros/")

        # Editar: denegado por servidor
        res_edit = self.client.get(f"/registros/{self.reg.pk}/editar/")
        self.assertRedirects(res_edit, "/registros/")

    def test_normal_user_can_create_but_cannot_edit_or_delete(self):
        self.client.login(username="normal_user", password="password123")

        # Crear GET y POST: permitido
        res_get_crear = self.client.get("/registros/crear/")
        self.assertEqual(res_get_crear.status_code, 200)

        res_post_crear = self.client.post("/registros/crear/", {
            "remitente": "nuevo@empresa.com",
            "asunto": "Urgente corte de base de datos",
            "cuerpo": "error 500 urgente",
            "prioridad": 5,
        })
        self.assertRedirects(res_post_crear, "/registros/")
        self.assertTrue(Registro.objects.filter(asunto="Urgente corte de base de datos").exists())

        # Editar: denegado
        res_edit = self.client.get(f"/registros/{self.reg.pk}/editar/")
        self.assertRedirects(res_edit, "/registros/")

        # Eliminar: denegado
        res_del = self.client.post(f"/registros/{self.reg.pk}/eliminar/")
        self.assertRedirects(res_del, "/registros/")

    def test_admin_can_edit_and_recalculates_decision(self):
        self.client.login(username="admin_user", password="password123")

        # Edición cambia contenido a crítico -> debe recalcular categoria con decidir()
        res_edit = self.client.post(f"/registros/{self.reg.pk}/editar/", {
            "remitente": "antiguo@empresa.com",
            "asunto": "Urgente caida general de servidores",
            "cuerpo": "El sistema no responde error 500 corte inmediato",
            "prioridad": 5,
        })
        self.assertRedirects(res_edit, "/registros/")

        self.reg.refresh_from_db()
        self.assertEqual(self.reg.categoria, "Ticket crítico")

    def test_admin_can_soft_delete(self):
        self.client.login(username="admin_user", password="password123")

        res_del = self.client.post(f"/registros/{self.reg.pk}/eliminar/")
        self.assertRedirects(res_del, "/registros/")

        self.reg.refresh_from_db()
        self.assertTrue(self.reg.eliminado)
        self.assertIsNotNone(self.reg.fecha_eliminacion)

    def test_login_and_logout_flow(self):
        # Login incorrecto
        res_fail = self.client.post("/login/", {"username": "viewer_user", "password": "wrongpassword"})
        self.assertEqual(res_fail.status_code, 200)
        self.assertContains(res_fail, "Usuario o contrasena incorrectos.")

        # Login correcto
        res_ok = self.client.post("/login/", {"username": "viewer_user", "password": "password123"})
        self.assertRedirects(res_ok, "/registros/")

        # Logout
        res_logout = self.client.get("/logout/")
        self.assertRedirects(res_logout, "/login/")

"""
URL configuration for rag_triage_mail project (Eva 2).
"""

from django.contrib import admin
from django.urls import path
from django.views.generic import RedirectView
from core import views

urlpatterns = [
    # Panel de administración de Django (Criterio 2.1.2)
    path("admin/", admin.site.urls),

    # Autenticación (Criterio 2.1.4)
    path("login/", views.vista_login, name="login"),
    path("logout/", views.vista_logout, name="logout"),

    # Operaciones CRUD (Criterio 2.1.3)
    path("registros/", views.lista, name="lista"),
    path("registros/crear/", views.crear, name="crear"),
    path("registros/<int:pk>/editar/", views.editar, name="editar"),
    path("registros/<int:pk>/eliminar/", views.eliminar, name="eliminar"),

    # Redirección raíz a la lista de registros
    path("", RedirectView.as_view(url="/registros/", permanent=False)),

    # Endpoints de compatibilidad con entrega anterior
    path("api/classify/", views.classify_email, name="classify-email"),
    path("api/reload/", views.reload_corpus, name="reload-corpus"),
    path("resumen/", views.resumen, name="resumen"),
]

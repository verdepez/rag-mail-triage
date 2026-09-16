from django.contrib import admin
from .models import Registro


@admin.register(Registro)
class RegistroAdmin(admin.ModelAdmin):
    list_display = (
        "remitente",
        "asunto",
        "categoria",
        "prioridad",
        "fecha",
        "eliminado",
    )
    list_filter = ("categoria", "eliminado")
    search_fields = ("remitente", "asunto")
    readonly_fields = ("fecha_eliminacion",)

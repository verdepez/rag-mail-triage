from django.db import models
from django.utils import timezone


class Registro(models.Model):
    CATEGORIA_CHOICES = [
        ("Ticket crítico", "Ticket crítico"),
        ("Requiere firma", "Requiere firma"),
        ("Informativo", "Informativo"),
        ("Dato inválido", "Dato inválido"),
    ]

    remitente = models.CharField(max_length=150, verbose_name="Remitente")
    asunto = models.CharField(max_length=200, verbose_name="Asunto")
    cuerpo = models.TextField(verbose_name="Cuerpo del mensaje")
    prioridad = models.IntegerField(default=1, verbose_name="Prioridad")
    categoria = models.CharField(
        max_length=50,
        choices=CATEGORIA_CHOICES,
        default="Informativo",
        verbose_name="Categoría",
    )
    resumen = models.CharField(
        max_length=255, blank=True, default="", verbose_name="Resumen"
    )
    accion_sugerida = models.CharField(
        max_length=255, blank=True, default="", verbose_name="Acción sugerida"
    )
    fecha = models.DateTimeField(default=timezone.now, verbose_name="Fecha de registro")

    # Borrado logico: no se pierde nada, solo se oculta
    eliminado = models.BooleanField(default=False, verbose_name="Eliminado")
    fecha_eliminacion = models.DateTimeField(
        null=True, blank=True, verbose_name="Fecha de eliminación"
    )

    class Meta:
        ordering = ["-fecha"]
        verbose_name = "Registro de correo"
        verbose_name_plural = "Registros de correos"

    def __str__(self):
        return f"{self.remitente} - {self.asunto} ({self.categoria})"

    def soft_delete(self):
        self.eliminado = True
        self.fecha_eliminacion = timezone.now()
        self.save()

    # Propiedades de compatibilidad con ejemplo genérico de la pauta INACAP
    @property
    def nombre(self):
        return self.remitente

    @nombre.setter
    def nombre(self, val):
        self.remitente = val

    @property
    def cantidad(self):
        return self.prioridad

    @cantidad.setter
    def cantidad(self, val):
        self.prioridad = val

    @property
    def estado(self):
        return self.categoria

    @estado.setter
    def estado(self, val):
        self.categoria = val

    @property
    def resultado(self):
        return self.categoria

    @resultado.setter
    def resultado(self, val):
        self.categoria = val

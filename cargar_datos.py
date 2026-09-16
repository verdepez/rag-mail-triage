"""
Script de migración: Transfiere los datos iniciales de datos.json a SQLite.
Soporta ejecución directa o vía Django shell:
    python cargar_datos.py
    python manage.py shell < cargar_datos.py
"""

import json
import os
import sys
from pathlib import Path

# Configurar Django si se ejecuta directamente
if not os.environ.get("DJANGO_SETTINGS_MODULE"):
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "miproyecto.settings")
    import django
    django.setup()

from core.models import Registro

json_path = Path("datos.json")
if not json_path.exists():
    print(f"[-] No se encontró el archivo {json_path}")
    sys.exit(1)

with open(json_path, "r", encoding="utf-8") as f:
    datos = json.load(f)

print(f"[i] Leyendo {len(datos)} elementos desde '{json_path}'...")

creados = 0
actualizados = 0

for r in datos:
    remitente = r.get("from", r.get("nombre", "desconocido@empresa.com")).strip()
    asunto = r.get("subject", r.get("resultado", "Sin asunto")).strip()
    cuerpo = r.get("body", "Sin contenido").strip()
    prioridad = int(r.get("priority_score", r.get("cantidad", 1)))
    categoria = r.get("category", r.get("estado", "Informativo")).strip()
    resumen = r.get("summary", f"Procesamiento sobre: {asunto}").strip()
    accion = r.get("suggested_action", "Revisar registro.").strip()

    obj, created = Registro.objects.get_or_create(
        remitente=remitente,
        asunto=asunto,
        defaults={
            "cuerpo": cuerpo,
            "prioridad": prioridad,
            "categoria": categoria,
            "resumen": resumen,
            "accion_sugerida": accion,
            "eliminado": False,
        },
    )
    if created:
        creados += 1
    else:
        # Sincronizar campos existentes si hubieran cambiado en el JSON
        obj.cuerpo = cuerpo
        obj.prioridad = prioridad
        obj.categoria = categoria
        obj.resumen = resumen
        obj.accion_sugerida = accion
        obj.save()
        actualizados += 1

print(f"\n[+] Migración exitosa:")
print(f"    - Creados:      {creados}")
print(f"    - Actualizados: {actualizados}")
print(f"    - Total en BD:  {Registro.objects.count()} (activos: {Registro.objects.filter(eliminado=False).count()})\n")

print("Listado actual en SQLite (db.sqlite3):")
print("-" * 80)
print(f"{'ID':<4} | {'Remitente':<26} | {'Categoría':<16} | {'Prio':<4} | {'Asunto'}")
print("-" * 80)
for reg in Registro.objects.filter(eliminado=False).order_by("pk"):
    print(f"#{reg.pk:<3} | {reg.remitente[:26]:<26} | {reg.categoria[:16]:<16} | {reg.prioridad:<4} | {reg.asunto[:30]}")
print("-" * 80)

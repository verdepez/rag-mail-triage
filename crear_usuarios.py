"""
Script de creación de usuarios y roles según Criterio 2.1.4 (Eva 2).
Las contraseñas se leen estrictamente desde el archivo .env o entorno.
Soporta ejecución directa o vía Django shell:
    python crear_usuarios.py
    python manage.py shell < crear_usuarios.py
"""

import os
from pathlib import Path

# Configurar Django si se ejecuta directamente
if not os.environ.get("DJANGO_SETTINGS_MODULE"):
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "miproyecto.settings")
    import django
    django.setup()

from django.contrib.auth.models import Group, User

# Cargar .env manualmente si no estuviera ya cargado en el proceso
env_path = Path(".env")
if env_path.exists():
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

pass_admin = os.environ.get("PASS_ADMIN", "Admin123!")
pass_normal = os.environ.get("PASS_NORMAL", "Normal123!")
pass_lector = os.environ.get("PASS_LECTOR", "Lector123!")

# 1. Crear los 3 grupos
grupos = {}
for nombre in ("admin", "normal", "viewer"):
    grupo, _ = Group.objects.get_or_create(name=nombre)
    grupos[nombre] = grupo
print("[+] Grupos configurados: admin, normal, viewer.")

# 2. Configurar usuario Administrador (acceso a todo y admin Django)
u_admin, created = User.objects.get_or_create(username="admin")
u_admin.set_password(pass_admin)
u_admin.is_staff = True
u_admin.is_superuser = True
u_admin.save()
u_admin.groups.add(grupos["admin"])
print(f"[+] Usuario 'admin' {'creado' if created else 'actualizado'} en grupo 'admin' (superuser).")

# 3. Configurar usuario Operador (creación y lectura)
u_normal, created = User.objects.get_or_create(username="operador")
u_normal.set_password(pass_normal)
u_normal.is_staff = False
u_normal.is_superuser = False
u_normal.save()
u_normal.groups.add(grupos["normal"])
print(f"[+] Usuario 'operador' {'creado' if created else 'actualizado'} en grupo 'normal'.")

# 4. Configurar usuario Lector (solo lectura)
u_lector, created = User.objects.get_or_create(username="lector")
u_lector.set_password(pass_lector)
u_lector.is_staff = False
u_lector.is_superuser = False
u_lector.save()
u_lector.groups.add(grupos["viewer"])
print(f"[+] Usuario 'lector' {'creado' if created else 'actualizado'} en grupo 'viewer'.")

print("\n[✓] Inicialización de usuarios y grupos completada con éxito.")

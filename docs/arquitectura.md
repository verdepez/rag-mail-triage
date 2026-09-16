# Arquitectura del Sistema (Eva 2)

## Componentes Principales

- `core/models.py`: Modelo relacional `Registro` con soporte de borrado lógico (`eliminado`, `fecha_eliminacion`, método `soft_delete`).
- `core/views.py`: Operaciones CRUD (`lista`, `crear`, `editar`, `eliminar`), autenticación (`vista_login`, `vista_logout`) y control de acceso con decorador `@requiere_rol`.
- `core/admin.py`: Configuración del panel de administración Django para `Registro` con columnas, filtros y búsqueda.
- `core/templates/`: Vistas de interfaz HTML (`lista.html`, `form.html`, `confirmar.html`, `login.html`) protegidas con `{% csrf_token %}`.
- `solucion.py`: Regla de decisión centralizada (`decidir`), sanitización de correos, RAG en memoria y cliente Ollama/fallback heurístico.
- `miproyecto/`: Configuración del proyecto Django (`settings.py` con SQLite y middlewares de auth/messages; `urls.py` con rutas CRUD y admin).
- `cargar_datos.py`: Migración de datos desde `datos.json` hacia SQLite.
- `crear_usuarios.py`: Configuración de roles/grupos (`admin`, `normal`, `viewer`) y usuarios con contraseñas desde variables de entorno.

## Flujo de Datos y Roles

```text
Usuario en Navegador
        │
        ▼
   [ /login/ ] ──> Autenticación (django.contrib.auth)
        │
        ▼
   [ /registros/ ] ──> Vista lista (Filtra eliminado=False)
        │
        ├── [ Crear ] (Roles: admin, normal) ──> Formulario ──> decidir() ──> Registro.objects.create()
        ├── [ Editar ] (Rol: admin) ──────────> Formulario ──> Recálculo decidir() ──> reg.save()
        └── [ Eliminar ] (Rol: admin) ────────> Confirmación ──> reg.soft_delete()
```

## Control de Acceso (Autorización en Servidor)

1. **`admin`**: Acceso total a ver, crear, editar y eliminar registros; superusuario en `/admin/`.
2. **`normal`**: Acceso a ver listado y crear nuevos registros.
3. **`viewer`**: Acceso de solo lectura al listado.

La seguridad reside en el servidor mediante el decorador `@requiere_rol(*roles)`. Las comprobaciones en las plantillas HTML son complementarias para mejorar la interfaz de usuario.
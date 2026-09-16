# PLAN DE IMPLEMENTACIÓN & OPENSPEC: SISTEMA DE TRIAGE DE CORREOS (EVA 2)

**Proyecto:** Sistema Django de Clasificación y Triage de Correos con Base de Datos y Control de Acceso por Roles  
**Evaluación:** Eva 2 (Criterios 2.1.1, 2.1.2, 2.1.3, 2.1.4) - INACAP TI3V41  
**Estado:** Implementado y Validado  

---

## 1. Problema
El personal administrativo enfrenta saturación operativa por el flujo masivo y heterogéneo de correos entrantes. En la entrega inicial (ES1), los datos se almacenaban en un archivo plano `datos.json` sin concurrencia ni control de acceso, lo que exponía la información a modificaciones no autorizadas y pérdida de trazabilidad. Se requiere una plataforma transaccional segura donde los datos vivan en una base de datos relacional y cada usuario opere según su rol asignado.

---

## 2. Solución Arquitectónica (Eva 2)
Evolucionar el sistema desde el almacenamiento en archivo plano hacia una arquitectura relacional con SQLite y Django ORM:
1. **Base de Datos y Modelo (`core/models.py`):** Modelo `Registro` con campos para remitente, asunto, cuerpo, prioridad y categoría, integrando borrado lógico (`eliminado`, `fecha_eliminacion`, `soft_delete()`) para preservar el archivo histórico sin eliminar físicamente información.
2. **Administración de Django (`core/admin.py`):** Panel administrativo completo con columnas personalizadas (`list_display`), filtros laterales (`list_filter`), buscador (`search_fields`) y campos de solo lectura (`readonly_fields`).
3. **Cuatro Operaciones CRUD (`core/views.py`):**
   - **Read (`lista`):** Listado de registros activos (`eliminado=False`).
   - **Create (`crear`):** Ingesta, validación y cálculo de categoría mediante la función de decisión `decidir()`.
   - **Update (`editar`):** Edición de datos y **recálculo obligatorio** de la categoría para evitar inconsistencias.
   - **Delete (`eliminar`):** Borrado lógico ejecutando `soft_delete()`.
4. **Control de Acceso y Roles (`core/views.py`):**
   - Autenticación nativa de Django (`vista_login`, `vista_logout`).
   - Roles gestionados mediante Grupos de Django: `admin`, `normal`, `viewer`.
   - Decorador de servidor `@requiere_rol(*roles)` que impide que usuarios de menor rango accedan a rutas no autorizadas mediante URL directa.
5. **Reutilización de Regla de Decisión:** La función `decidir()` en `solucion.py` se mantiene intacta y se importa directamente en las vistas, centralizando la lógica de negocio sin duplicación de código.

---

## 3. Alcance

* **Motor de Base de Datos:** SQLite (`db.sqlite3`), gestionado a través de migraciones nativas de Django (`makemigrations`, `migrate`).
* **Seguridad en Servidor:** Autorización estricta por decorador en servidor; los condicionales en plantillas (`{% if %}`) son meramente cosméticos.
* **Borrado Lógico:** Marcado con `eliminado = True` y registro de fecha/hora de baja, sin pérdida de datos.
* **Gestión de Secretos:** `SECRET_KEY` y contraseñas de usuarios leídas desde `.env`, nunca hardcodeadas.

---

## 4. Matriz MoSCoW (Eva 2)

| Categoría | Requerimientos |
| :--- | :--- |
| **Must Have** *(Imprescindible)* | • Base de datos relacional SQLite configurada en `miproyecto/settings.py`.<br>• Modelo `Registro` con borrado lógico (`soft_delete`, `eliminado`, `fecha_eliminacion`).<br>• Panel administrativo de Django con `list_display`, filtros, búsqueda y campos de solo lectura.<br>• Operaciones CRUD completas (`lista`, `crear`, `editar`, `eliminar`) con recálculo de decisión en edición.<br>• Autenticación (`login`, `logout`) y roles por grupos (`admin`, `normal`, `viewer`) con decorador `@requiere_rol`.<br>• Formularios protegidos con `{% csrf_token %}`.<br>• Reutilización de regla de decisión intacta desde `solucion.py`. |
| **Should Have** *(Importante)* | • Script `cargar_datos.py` para migrar los registros previos de `datos.json` a la base de datos.<br>• Script `crear_usuarios.py` para aprovisionar roles y usuarios leyendo contraseñas de `.env`.<br>• Suite de pruebas unitarias automatizadas (`core/tests.py`) validando CRUD, roles y modelo. |
| **Could Have** *(Deseable)* | • Visualización de badges diferenciados por categoría y prioridad en el listado HTML.<br>• Compatibilidad backward con endpoints JSON existentes (`/api/classify/`). |
| **Won't Have** *(Fuera de alcance)* | • Motores de bases de datos externos pesados (PostgreSQL, MySQL, Oracle).<br>• Modelos de usuario personalizados o contraseñas almacenadas fuera de `django.contrib.auth`.<br>• Autorización delegada exclusivamente a la plantilla sin validación en servidor. |

---

## 5. Especificación de Endpoints y Vistas

| Ruta | Nombre | Método | Rol Mínimo | Descripción |
| :--- | :--- | :--- | :--- | :--- |
| `/login/` | `login` | GET / POST | Anónimo | Autenticación de usuarios con mensajes flash |
| `/logout/` | `logout` | GET / POST | Autenticado | Cierre de sesión y redirección a login |
| `/registros/` | `lista` | GET | `viewer` | Listado de registros activos (`eliminado=False`) |
| `/registros/crear/` | `crear` | GET / POST | `normal` | Formulario de creación y clasificación automática |
| `/registros/<pk>/editar/` | `editar` | GET / POST | `admin` | Edición con recálculo de la regla de decisión |
| `/registros/<pk>/eliminar/` | `eliminar` | GET / POST | `admin` | Confirmación y ejecución de borrado lógico |
| `/admin/` | `admin:index` | GET / POST | Superuser | Panel administrativo de Django |
# RAG Mail Triage — Eva 2

Sistema web en **Django** para la clasificación, triage y gestión de correos electrónicos administrativos y operativos, desarrollado para la **Evaluación 2 (Unidad 2: Programación Back End - INACAP TI3V41)**.

Evolucionado desde la entrega inicial (ES1), el sistema ahora incorpora persistencia relacional en **SQLite con ORM de Django**, operaciones **CRUD completas con borrado lógico**, panel administrativo personalizado, autenticación nativa y **control de acceso basado en roles** (`admin`, `normal`, `viewer`) con validación estricta en el servidor mediante decoradores.

---

## 🚀 Novedades y Alcance (Eva 2)

- **Persistencia en SQLite (Criterio 2.1.1):** Reemplazo del almacenamiento plano en JSON por una base de datos relacional SQLite (`db.sqlite3`) administrada mediante migraciones de Django.
- **Borrado Lógico (Criterio 2.1.1):** Las bajas de registros no eliminan información; marcan el campo `eliminado = True`, estampan la `fecha_eliminacion` mediante el método `soft_delete()` y preservan la trazabilidad histórica.
- **Panel de Administración (Criterio 2.1.2):** Integración en `/admin/` con personalización avanzada (`list_display`, filtros por categoría y estado de eliminación, buscador y campos de solo lectura).
- **Operaciones CRUD Web (Criterio 2.1.3):**
  - **Read:** Listado de registros activos filtrados (`eliminado=False`) con badges por categoría y prioridad.
  - **Create:** Ingesta de correos con validación de datos y clasificación automática.
  - **Update:** Edición de remitente, asunto y contenido con **recálculo obligatorio** de la regla de decisión para evitar inconsistencias.
  - **Delete:** Interfaz de confirmación y ejecución de borrado lógico.
- **Autenticación y Roles en Servidor (Criterio 2.1.4):**
  - Sistema de usuarios nativo de Django (`auth`).
  - Roles implementados mediante Grupos: `admin`, `normal`, `viewer`.
  - Decorador `@requiere_rol(*roles)` aplicado en el servidor: un usuario de menor rango no puede saltarse las restricciones escribiendo URLs directas a mano en el navegador.
- **Regla de Decisión Intacta:** La lógica de sanitización y clasificación (RAG TF-IDF + inferencia Ollama/fallback heurístico) en `solucion.py` se mantiene intacta y se importa en las vistas mediante `decidir()`.

---

## 👥 Matriz de Roles y Permisos

| Rol | Grupo Django | Ver Listado | Crear Registros | Editar Registros | Eliminar (Lógico) | Panel `/admin/` |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Administrador** | `admin` | ✅ | ✅ | ✅ *(con recálculo)* | ✅ | ✅ *(Superuser)* |
| **Operador** | `normal` | ✅ | ✅ | ❌ *(Rechazado en servidor)* | ❌ *(Rechazado)* | ❌ |
| **Lector** | `viewer` | ✅ | ❌ *(Rechazado)* | ❌ *(Rechazado)* | ❌ *(Rechazado)* | ❌ |

---

## 📋 Requisitos Previos

- Python 3.11 o superior
- Entorno virtual (`venv`)
- SQLite3 (incluido en la biblioteca estándar de Python)
- (Opcional) Ollama en ejecución local para inferencia generativa con LLM

---

## 🛠️ Instalación y Puesta en Marcha (Clon Limpio)

Sigue estos pasos para levantar el proyecto desde cero:

### 1. Clonar el repositorio y navegar a la carpeta
```bash
git clone <URL_DEL_REPOSITORIO>
cd rag-mail-triage
```

### 2. Crear y activar el entorno virtual
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno
Copia el archivo de ejemplo:
```bash
cp .env.example .env
```
Edita `.env` con tus claves locales. Ejemplo de configuración para desarrollo:
```env
SECRET_KEY=clave_segura_para_desarrollo_local
DEBUG=True
PASS_ADMIN=Admin123!
PASS_NORMAL=Normal123!
PASS_LECTOR=Lector123!
```
*(Nota: `.env` está en `.gitignore` y jamás debe subirse al repositorio).*

### 5. Aplicar migraciones a la base de datos
```bash
python manage.py migrate
```

### 6. Poblar datos iniciales y crear usuarios de prueba
```bash
# 6.1 Cargar los correos históricos desde datos.json a SQLite
python cargar_datos.py

# 6.2 Crear los grupos de roles y los usuarios desde las contraseñas del .env
python crear_usuarios.py
```

### 7. Iniciar el servidor de desarrollo
```bash
python manage.py runserver
```

---

## 🔐 Credenciales de Prueba Preconfiguradas

Una vez ejecutado `crear_usuarios.py`, puedes ingresar en [http://127.0.0.1:8000/login/](http://127.0.0.1:8000/login/) con:

| Usuario | Contraseña | Rol / Grupo | Comportamiento Esperado |
| :--- | :--- | :--- | :--- |
| `admin` | `Admin123!` | `admin` | Acceso total al CRUD y al panel de administración `/admin/`. |
| `operador` | `Normal123!` | `normal` | Puede ver la lista y crear registros; al intentar editar o borrar es rechazado. |
| `lector` | `Lector123!` | `viewer` | Solo lectura; al intentar crear, editar o borrar es rechazado por el servidor. |

---

## 🌐 Mapa de Rutas

| Ruta | Nombre | Método | Rol Mínimo | Descripción |
| :--- | :--- | :---: | :---: | :--- |
| `/login/` | `login` | GET / POST | Anónimo | Formulario de autenticación con mensajes de error |
| `/logout/` | `logout` | GET | Autenticado | Cierre de sesión y redirección a login |
| `/registros/` | `lista` | GET | `viewer` | Bandeja de triage con registros activos |
| `/registros/crear/` | `crear` | GET / POST | `normal` | Formulario de creación con clasificación automática |
| `/registros/<pk>/editar/` | `editar` | GET / POST | `admin` | Edición de registro con recálculo mandatorio de categoría |
| `/registros/<pk>/eliminar/` | `eliminar` | GET / POST | `admin` | Confirmación y ejecución de borrado lógico |
| `/admin/` | `admin:index` | GET / POST | Superuser | Panel administrativo de Django |
| `/` | - | GET | - | Redirección automática a `/registros/` |

---

## 🧪 Ejecución de Pruebas Automatizadas

El proyecto cuenta con una suite completa de pruebas unitarias y de integración en `core/tests.py` que validan el modelo, borrado lógico, operaciones CRUD, recálculo de categoría y rechazo de rutas por rol en servidor:

```bash
# Ejecutar suite de pruebas de Django
python manage.py test core

# Comprobar que no existan migraciones pendientes
python manage.py makemigrations --check --dry-run
```

---

## 📁 Estructura del Proyecto

```text
rag-mail-triage/
├── core/                       # Aplicación principal
│   ├── migrations/             # Migraciones de base de datos
│   ├── templates/              # Plantillas HTML (lista, form, confirmar, login)
│   ├── admin.py                # Configuración de Django Admin para Registro
│   ├── models.py               # Modelo Registro con borrado lógico (soft_delete)
│   ├── tests.py                # Suite de pruebas unitarias e integración
│   └── views.py                # Vistas CRUD, autenticación y decorador @requiere_rol
├── miproyecto/                 # Configuración del proyecto Django
│   ├── settings.py             # Configuración SQLite, middlewares de auth y .env
│   ├── urls.py                 # Enrutamiento de URLs (admin, crud, auth)
│   └── wsgi.py
├── cargar_datos.py             # Script de migración de datos.json a SQLite
├── crear_usuarios.py           # Script de aprovisionamiento de roles y usuarios
├── datos.json                  # Corpus histórico de correos
├── solucion.py                 # Motor RAG TF-IDF, Ollama, fallback y función decidir()
├── plan.md                     # Plan de implementación y especificación OpenSpec
├── ia.md                       # Registro de consultas y correcciones sobre la IA
├── requirements.txt            # Dependencias del proyecto
├── .env.example                # Plantilla de variables de entorno requeridas
└── .gitignore                  # Exclusiones seguras en UTF-8 (.env, .venv, db.sqlite3)
```

---

## 📄 Documentación de Entrega

- **[plan.md](plan.md):** Plan de implementación con alcance real (SQLite, CRUD, roles, borrado lógico y matriz MoSCoW actualizada).
- **[ia.md](ia.md):** Trazabilidad del uso de Inteligencia Artificial (herramientas, consultas textuales y correcciones críticas aplicadas).

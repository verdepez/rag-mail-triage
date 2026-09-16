# Registro de Interacción con Inteligencia Artificial (Eva 2)

## 1. Herramienta Utilizada
- **Herramienta:** Google Antigravity (asistente de ingeniería de software asistido por LLM).

## 2. Consultas Textuales Realizadas

### Consulta 1 (Modelo y Migraciones):
> *"¿Cómo diseño el modelo Registro para persistir los datos de triage en SQLite con borrado lógico y cómo ejecuto las migraciones sin romper compatibilidad con datos.json?"*

### Consulta 2 (Roles y Autorización):
> *"¿Cómo implemento los roles admin, normal y viewer en Django para que un usuario de rol bajo no pueda editar ni borrar registros aunque conozca la URL directa?"*

### Consulta 3 (Edición y Regla de Negocio):
> *"Al actualizar un correo existente en la vista de edición, ¿cómo aseguro que la categoría asignada refleje los nuevos cambios ingresados en el formulario?"*

## 3. Correcciones Críticas Aplicadas a las Respuestas de la IA

1. **Evitar modelos de usuario propios y contraseñas inseguras:**
   - *Propuesta inicial de la IA:* Sugirió crear un modelo de usuario propio con un campo de texto `rol` y contraseñas almacenadas directamente.
   - *Corrección aplicada:* Se descartó de inmediato. Se utilizó el sistema nativo `django.contrib.auth` con `User` y `Group` (`admin`, `normal`, `viewer`), parametrizando las contraseñas exclusivamente a través de variables de entorno en `.env`, tal como exige el estándar de seguridad de Django y la pauta de evaluación.

2. **Evitar bases de datos externas innecesarias:**
   - *Propuesta inicial de la IA:* Propuso configurar un contenedor Docker con PostgreSQL y dependencias complejas.
   - *Corrección aplicada:* Se instruyó mantener la base SQLite integrada que provee Django (`BASE_DIR / 'db.sqlite3'`), simplificando el despliegue local y cumpliendo con el Criterio 2.1.1.

3. **Seguridad real en servidor vs. ocultamiento visual en plantilla:**
   - *Propuesta inicial de la IA:* Sugirió ocultar los botones de «Editar» y «Eliminar» en la plantilla HTML únicamente con condicionales `{% if es_admin %}`.
   - *Corrección aplicada:* Se exigió la implementación del decorador `@requiere_rol(*roles)` a nivel de vista en el servidor. Aunque el botón se oculte en la interfaz para mejorar la experiencia de usuario, si un atacante o usuario de menor rango escribe la ruta `/registros/1/editar/` a mano en la barra de navegación, el servidor valida el grupo y rechaza la petición con una redirección y mensaje de error.

4. **Recálculo mandatorio de la decisión:**
   - *Propuesta inicial de la IA:* En la vista `editar`, actualizaba únicamente los campos editados guardando el modelo sin reevaluar la clasificación.
   - *Corrección aplicada:* Se obligó a invocar `reg.categoria = decidir(...)` antes de `reg.save()` para evitar inconsistencias donde el texto cambia pero la categoría queda obsoleta.

import json
from functools import wraps
from uuid import uuid4

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from solucion import analyze_email, decidir, get_rag_engine
from .models import Registro


# ==========================================
# 1. CONTROL DE ACCESO BASADO EN ROLES
# ==========================================
def tiene_rol(user, *roles):
    """Comprueba si el usuario pertenece a alguno de los roles indicados o es superusuario."""
    if not user.is_authenticated:
        return False
    return user.groups.filter(name__in=roles).exists() or user.is_superuser


def requiere_rol(*roles):
    """Decorador de servidor que restringe el acceso según el grupo/rol del usuario."""
    def decorador(view_func):
        @wraps(view_func)
        @login_required(login_url="login")
        def wrapper(request, *args, **kwargs):
            if tiene_rol(request.user, *roles):
                return view_func(request, *args, **kwargs)
            messages.error(request, "No tienes permiso para esta accion.")
            return redirect("lista")
        return wrapper
    return decorador


# ==========================================
# 2. AUTENTICACIÓN
# ==========================================
def vista_login(request):
    if request.user.is_authenticated:
        return redirect("lista")
    if request.method == "POST":
        user = authenticate(
            request,
            username=request.POST.get("username", "").strip(),
            password=request.POST.get("password", ""),
        )
        if user:
            login(request, user)
            return redirect("lista")
        messages.error(request, "Usuario o contrasena incorrectos.")
    return render(request, "login.html")


def vista_logout(request):
    logout(request)
    return redirect("login")


# ==========================================
# 3. VISTAS CRUD (Criterio 2.1.3)
# ==========================================
@login_required(login_url="login")
def lista(request):  # READ
    registros = Registro.objects.filter(eliminado=False)
    es_admin = tiene_rol(request.user, "admin")
    es_normal = tiene_rol(request.user, "normal")
    return render(
        request,
        "lista.html",
        {
            "registros": registros,
            "es_admin": es_admin,
            "puede_crear": es_admin or es_normal,
        },
    )


@requiere_rol("admin", "normal")
def crear(request):  # CREATE
    error = None
    if request.method == "POST":
        remitente = request.POST.get(
            "remitente", request.POST.get("nombre", "")
        ).strip()
        asunto = request.POST.get("asunto", "").strip()
        cuerpo = request.POST.get("cuerpo", "").strip()
        prioridad_raw = request.POST.get(
            "prioridad", request.POST.get("cantidad", "1")
        ).strip()

        if not remitente or not asunto or not cuerpo:
            error = "Todos los campos (remitente, asunto, cuerpo) son obligatorios."
        else:
            try:
                prioridad = int(prioridad_raw)
            except ValueError:
                error = "La cantidad o prioridad debe ser un numero entero."
            else:
                categoria = decidir(asunto, cuerpo, remitente)
                Registro.objects.create(
                    remitente=remitente,
                    asunto=asunto,
                    cuerpo=cuerpo,
                    prioridad=prioridad,
                    categoria=categoria,
                    resumen=f"Procesamiento sobre: {asunto}",
                    accion_sugerida="Gestión automática según categoría asignada.",
                )
                messages.success(request, "Registro creado exitosamente.")
                return redirect("lista")

    return render(request, "form.html", {"accion": "Crear", "error": error})


@requiere_rol("admin")
def editar(request, pk):  # UPDATE
    reg = get_object_or_404(Registro, pk=pk, eliminado=False)
    error = None
    if request.method == "POST":
        remitente = request.POST.get(
            "remitente", request.POST.get("nombre", "")
        ).strip()
        asunto = request.POST.get("asunto", "").strip()
        cuerpo = request.POST.get("cuerpo", "").strip()
        prioridad_raw = request.POST.get(
            "prioridad", request.POST.get("cantidad", str(reg.prioridad))
        ).strip()

        if not remitente or not asunto or not cuerpo:
            error = "Todos los campos son obligatorios."
        else:
            try:
                prioridad = int(prioridad_raw)
            except ValueError:
                error = "La cantidad o prioridad debe ser un numero entero."
            else:
                reg.remitente = remitente
                reg.asunto = asunto
                reg.cuerpo = cuerpo
                reg.prioridad = prioridad
                # Recalcular la decisión con la función decidir()
                reg.categoria = decidir(reg.asunto, reg.cuerpo, reg.remitente)
                reg.resumen = f"Procesamiento sobre: {reg.asunto}"
                reg.save()
                messages.success(request, "Registro actualizado exitosamente.")
                return redirect("lista")

    return render(
        request, "form.html", {"accion": "Editar", "registro": reg, "error": error}
    )


@requiere_rol("admin")
def eliminar(request, pk):  # DELETE logico
    reg = get_object_or_404(Registro, pk=pk, eliminado=False)
    if request.method == "POST":
        reg.soft_delete()
        messages.success(request, f"Registro '{reg.asunto}' eliminado correctamente.")
        return redirect("lista")
    return render(request, "confirmar.html", {"registro": reg})


# ==========================================
# 4. COMPATIBILIDAD API JSON Y RESUMEN
# ==========================================
def classify_email(request):
    """Endpoint API JSON para clasificar correos."""
    if request.method != "POST":
        return JsonResponse({"error": "Usa el método POST."}, status=405)
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "El cuerpo debe ser JSON válido."}, status=400)
    if not isinstance(payload, dict):
        return JsonResponse({"error": "El payload debe ser un objeto JSON."}, status=400)

    engine = get_rag_engine()
    result = analyze_email(payload, engine)
    if result.get("category") != "Dato inválido":
        Registro.objects.get_or_create(
            remitente=payload.get("from", ""),
            asunto=payload.get("subject", ""),
            defaults={
                "cuerpo": payload.get("body", ""),
                "prioridad": result.get("priority", 1),
                "categoria": result.get("category", "Informativo"),
                "resumen": result.get("summary", ""),
                "accion_sugerida": result.get("suggested_action", ""),
            },
        )
    return JsonResponse(result)


def reload_corpus(request):
    """Endpoint para informar cantidad de registros activos."""
    if request.method != "POST":
        return JsonResponse({"error": "Usa el método POST."}, status=405)
    total = Registro.objects.filter(eliminado=False).count()
    return JsonResponse({"status": "ok", "records_loaded": total})


def resumen(request):
    """Redirección de la vista anterior al CRUD unificado."""
    return redirect("lista")

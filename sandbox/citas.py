import json
import re
import uuid
from datetime import datetime, date, timedelta
from decimal import Decimal
from django.db import transaction
from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from oscar.apps.catalogue.models import Product, ProductClass, Category, ProductCategory
from oscar.apps.partner.models import Partner, StockRecord
from citas_app.models import Cita

HORARIOS_MANANA = ["10:00 AM", "11:00 AM", "12:00 PM"]
HORARIOS_TARDE = [
    "02:00 PM", "03:00 PM", "04:00 PM", "05:00 PM",
    "06:00 PM", "07:00 PM", "08:00 PM", "09:00 PM", "10:00 PM"
]
HORARIOS_DISPONIBLES = HORARIOS_MANANA + HORARIOS_TARDE

CORTES_PRECIOS = {
    "Corte Clásico a Tijera y Máquina": Decimal("25.00"),
    "Degradado / Fade (Low, Mid o High)": Decimal("30.00"),
    "Mullet / Taper Fade Moderno": Decimal("32.00"),
    "Corte + Perfilado de Barba con Toalla Caliente": Decimal("45.00"),
    "Corte Infantil (Hasta 12 años)": Decimal("20.00"),
}

def aplicar_tolerancia_15_min():
    ahora = datetime.now()
    for cita in Cita.objects.filter(estado="50% Pagado"):
        try:
            dt_cita = datetime.strptime(f"{cita.fecha.strftime('%Y-%m-%d')} {cita.hora}", "%Y-%m-%d %I:%M %p")
            if ahora > dt_cita + timedelta(minutes=15):
                cita.estado = "Libre (+15m Tolerancia)"
                cita.save(update_fields=["estado"])
        except ValueError:
            continue

def vista_reservar_cita(request):
    aplicar_tolerancia_15_min()
    mensaje = None
    error = None

    cortes_info = [
        {
            "nombre": nombre,
            "precio": f"{precio:.2f}",
            "adelanto": f"{(precio / Decimal('2')):.2f}",
        }
        for nombre, precio in CORTES_PRECIOS.items()
    ]

    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip()
        telefono = re.sub(r"\s+", "", request.POST.get("telefono", "").strip())
        fecha_str = request.POST.get("fecha", "").strip()
        hora = request.POST.get("hora", "").strip()
        servicio = request.POST.get("servicio", "").strip()
        metodo_pago = request.POST.get("metodo_pago", "").strip()
        codigo_operacion = request.POST.get("codigo_operacion", "").strip()

        try:
            fecha_obj = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except ValueError:
            fecha_obj = None

        ahora = datetime.now()

        if not (nombre and telefono and fecha_obj and hora and servicio):
            error = "Por favor completa todos los campos y selecciona una hora."
        elif not re.match(r"^9\d{8}$", telefono):
            error = "Ingresa un número de celular válido de 9 dígitos (ejemplo: 987654321)."
        elif servicio not in CORTES_PRECIOS:
            error = "El servicio seleccionado no es válido."
        elif fecha_obj < ahora.date():
            error = "No puedes reservar una cita en una fecha pasada."
        elif fecha_obj.weekday() == 6:
            error = "Atendemos de Lunes a Sábado. Por favor elige otro día."
        elif hora not in HORARIOS_DISPONIBLES:
            error = "Horario no disponible (De 1:00 PM a 2:00 PM es horario de almuerzo)."
        elif not metodo_pago or len(codigo_operacion) < 4:
            error = "Debes abonar el 50% e ingresar un N° de operación válido (mínimo 4 caracteres)."
        else:
            dt_seleccionado = datetime.strptime(f"{fecha_str} {hora}", "%Y-%m-%d %I:%M %p")
            if dt_seleccionado < ahora:
                error = "Esa hora de hoy ya pasó. Por favor selecciona un turno futuro."
            else:
                with transaction.atomic():
                    ocupado = Cita.objects.select_for_update().filter(
                        fecha=fecha_obj,
                        hora=hora
                    ).exclude(estado="Libre (+15m Tolerancia)").exists()

                    if ocupado:
                        error = f"El turno de las {hora} el {fecha_str} ya fue reservado. Elige otra hora."
                    else:
                        precio_total = CORTES_PRECIOS[servicio]
                        adelanto = precio_total / Decimal("2")
                        saldo = precio_total - adelanto

                        Cita.objects.create(
                            nombre=nombre,
                            telefono=telefono,
                            fecha=fecha_obj,
                            hora=hora,
                            servicio=servicio,
                            precio_total=precio_total,
                            adelanto_pagado=adelanto,
                            saldo_pendiente=saldo,
                            metodo_pago=metodo_pago,
                            codigo_operacion=codigo_operacion,
                            estado="50% Pagado",
                        )
                        mensaje = (
                            f"¡Turno confirmado para {nombre} el {fecha_str} a las {hora}! "
                            f"Adelanto verificado: S/ {adelanto:.2f} ({metodo_pago} #{codigo_operacion}). "
                            f"Tolerancia máxima: 15 min. Saldo en local: S/ {saldo:.2f}."
                        )

    citas_ocupadas = Cita.objects.exclude(estado="Libre (+15m Tolerancia)").order_by("-fecha", "-hora")
    citas_publicas_json = json.dumps([
        {"fecha": c.fecha.strftime("%Y-%m-%d"), "hora": c.hora}
        for c in citas_ocupadas
    ])

    return render(request, "oscar/citas_fercho.html", {
        "horarios_manana": HORARIOS_MANANA,
        "horarios_tarde": HORARIOS_TARDE,
        "cortes": cortes_info,
        "cortes_json": json.dumps({k: float(v) for k, v in CORTES_PRECIOS.items()}),
        "citas": citas_ocupadas[:8],
        "citas_json": citas_publicas_json,
        "hoy_iso": date.today().strftime("%Y-%m-%d"),
        "mensaje": mensaje,
        "error": error,
    })

@staff_member_required(login_url="/es/dashboard/login/")
def vista_panel_barbero(request):
    aplicar_tolerancia_15_min()

    if request.method == "POST":
        accion = request.POST.get("accion")

        # Crear producto en 1 paso (solo nombre, precio y cantidad)
        if accion == "crear_producto":
            titulo = request.POST.get("titulo", "").strip()
            precio_str = request.POST.get("precio", "0").strip()
            stock_str = request.POST.get("stock", "0").strip()
            try:
                precio = Decimal(precio_str)
                stock = int(stock_str)
                if titulo and precio > 0 and stock >= 0:
                    clase, _ = ProductClass.objects.get_or_create(
                        name="Producto Físico Barbería",
                        defaults={"requires_shipping": True, "track_stock": True}
                    )
                    partner, _ = Partner.objects.get_or_create(name="Barbería Fercho")
                    categoria = Category.objects.first()
                    sku = f"FER-{uuid.uuid4().hex[:6].upper()}"

                    prod = Product.objects.create(
                        title=titulo,
                        upc=sku,
                        product_class=clase,
                        structure=Product.STANDALONE,
                        is_public=True,
                    )
                    if categoria:
                        ProductCategory.objects.create(product=prod, category=categoria)

                    StockRecord.objects.create(
                        product=prod,
                        partner=partner,
                        partner_sku=sku,
                        price_currency="PEN",
                        price=precio,
                        num_in_stock=stock,
                    )
            except Exception:
                pass
            return redirect("/panel-barbero/#inventario")

        # Botones rápidos de stock (+1, +5, -1 o guardar número exacto)
        elif accion in ("sumar_1", "sumar_5", "restar_1", "fijar_stock"):
            stock_id = request.POST.get("stock_id")
            registro = StockRecord.objects.filter(id=stock_id).first()
            if registro:
                if accion == "sumar_1":
                    registro.num_in_stock += 1
                elif accion == "sumar_5":
                    registro.num_in_stock += 5
                elif accion == "restar_1" and registro.num_in_stock > 0:
                    registro.num_in_stock -= 1
                elif accion == "fijar_stock":
                    try:
                        nuevo = int(request.POST.get("nuevo_stock", registro.num_in_stock))
                        if nuevo >= 0:
                            registro.num_in_stock = nuevo
                    except ValueError:
                        pass
                registro.save(update_fields=["num_in_stock"])
            return redirect("/panel-barbero/#inventario")

        # Control de citas
        else:
            cita_id = request.POST.get("cita_id")
            cita = Cita.objects.filter(id=cita_id).first()
            if cita:
                if accion == "iniciar" and cita.estado == "50% Pagado":
                    cita.estado = "En Corte"
                    cita.hora_inicio_real = datetime.now().strftime("%I:%M %p")
                    cita.save()
                elif accion == "completar" and cita.estado in ("50% Pagado", "En Corte"):
                    cita.estado = "Pagada"
                    cita.save()
                elif accion == "liberar" and cita.estado == "50% Pagado":
                    cita.estado = "Libre (+15m Tolerancia)"
                    cita.save()
            return redirect("panel_barbero")

    fecha_filtro = request.GET.get("fecha", "").strip()
    qs = Cita.objects.all()
    if fecha_filtro:
        qs = qs.filter(fecha=fecha_filtro)

    activas = qs.exclude(estado="Libre (+15m Tolerancia)")
    total_adelantos = sum((c.adelanto_pagado for c in activas), Decimal("0.00"))
    total_por_cobrar = sum(
        (c.saldo_pendiente for c in activas.filter(estado__in=["50% Pagado", "En Corte"])),
        Decimal("0.00")
    )

    # Mostrar TODOS los productos de la tienda sin duplicados
    productos_stock = []
    vistos = set()
    for sr in StockRecord.objects.select_related("product").exclude(
        product__product_class__name="Servicio de Corte"
    ).order_by("product__title"):
        if sr.product_id not in vistos:
            vistos.add(sr.product_id)
            productos_stock.append(sr)

    return render(request, "oscar/panel_barbero.html", {
        "citas": qs,
        "fecha_filtro": fecha_filtro,
        "total_adelantos": f"{total_adelantos:.2f}",
        "total_por_cobrar": f"{total_por_cobrar:.2f}",
        "total_citas": activas.count(),
        "productos_stock": productos_stock,
    })
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
django.setup()

from decimal import Decimal
from django.contrib.sites.models import Site
from oscar.apps.catalogue.categories import create_from_breadcrumbs
from oscar.apps.catalogue.models import ProductClass, Product, ProductCategory
from oscar.apps.partner.models import Partner, StockRecord
from oscar.apps.shipping.models import OrderAndItemCharges
from oscar.apps.address.models import Country

# 1. Actualizar nombre del Sitio a Barbería Fercho
site = Site.objects.get_current()
site.name = "Barbería Fercho"
site.domain = "127.0.0.1:8000"
site.save()

# 2. País base (Perú)
Country.objects.get_or_create(
    iso_3166_1_a2="PE",
    defaults={
        "iso_3166_1_a3": "PER",
        "iso_3166_1_numeric": "604",
        "printable_name": "Peru",
        "name": "Republic of Peru",
        "is_shipping_country": True,
    },
)

# 3. Proveedor / Sede
partner, _ = Partner.objects.get_or_create(name="Sede Principal Barbería Fercho")

# 4. Tipos de Producto: Cortes (Sin envío) vs Productos (Con envío)
clase_corte, _ = ProductClass.objects.get_or_create(
    name="Servicio de Corte",
    defaults={"requires_shipping": False, "track_stock": False},
)
clase_producto, _ = ProductClass.objects.get_or_create(
    name="Producto Físico Barbería",
    defaults={"requires_shipping": True, "track_stock": True},
)

# 5. Categorías (Priorizando Cortes primero)
cat_cortes = create_from_breadcrumbs("Servicios de Cortes")
cat_barba = create_from_breadcrumbs("Productos > Cuidado de Barba")
cat_cabello = create_from_breadcrumbs("Productos > Cabello y Peinado")
cat_herramientas = create_from_breadcrumbs("Productos > Herramientas y Afeitado")

# 6. Catálogo de Cortes (Prioridad #1)
cortes = [
    ("Corte Clásico a Tijera y Máquina", "CORTE-01", "25.00",
     "Corte tradicional con acabado limpio, lavado capilar y peinado con pomada."),
    ("Degradado / Fade (Low, Mid o High)", "CORTE-02", "30.00",
     "Desvanecido de alta precisión con navaja, perfilado de cerquillo y styling."),
    ("Corte + Perfilado de Barba con Toalla Caliente", "CORTE-03", "45.00",
     "Servicio completo: corte a elección + ritual de barba con vapor, toalla caliente y aceite esencial."),
    ("Mullet / Taper Fade Moderno", "CORTE-04", "32.00",
     "Texturizado moderno adaptado a la forma del rostro con acabado mate."),
    ("Corte Infantil (Hasta 12 años)", "CORTE-05", "20.00",
     "Corte cómodo, rápido y estilizado para niños."),
]

for titulo, sku, precio, desc in cortes:
    prod, _ = Product.objects.update_or_create(
        upc=sku,
        defaults={
            "title": titulo,
            "product_class": clase_corte,
            "description": desc,
            "is_public": True,
        },
    )
    ProductCategory.objects.get_or_create(product=prod, category=cat_cortes)
    StockRecord.objects.update_or_create(
        product=prod,
        partner=partner,
        defaults={
            "partner_sku": sku,
            "price_currency": "PEN",
            "price": Decimal(precio),
            "num_in_stock": 999,
        },
    )

# 7. Catálogo de Productos Físicos
productos = [
    ("Aceite Hidratante para Barba Sándalo 30ml", "BARB-001", cat_barba, "45.00", 25,
     "Aceite esencial natural para suavizar, nutrir y dar brillo a la barba."),
    ("Bálsamo Moldeador de Barba Clásico 60g", "BARB-002", cat_barba, "52.00", 20,
     "Fijación media con cera de abeja y manteca de karité."),
    ("Cera Mate Fijación Fuerte 100g", "CAB-001", cat_cabello, "38.00", 40,
     "Cera moldeadora a base de agua con acabado totalmente natural."),
    ("Pomada Clásica Brillo Medio 100g", "CAB-002", cat_cabello, "42.00", 30,
     "Ideal para peinados clásicos tipo pompadour o slick back."),
    ("Navaja Barbera Acero Inoxidable Profesional", "HERR-001", cat_herramientas, "65.00", 15,
     "Porta navajas ergonómico con mango antideslizante."),
    ("Kit Tijeras de Corte y Entresacar 6.0 Pulgadas", "HERR-002", cat_herramientas, "120.00", 10,
     "Acero japonés de alta durabilidad con estuche protector."),
]

for titulo, sku, categoria, precio, stock, desc in productos:
    prod, _ = Product.objects.update_or_create(
        upc=sku,
        defaults={
            "title": titulo,
            "product_class": clase_producto,
            "description": desc,
            "is_public": True,
        },
    )
    ProductCategory.objects.get_or_create(product=prod, category=categoria)
    StockRecord.objects.update_or_create(
        product=prod,
        partner=partner,
        defaults={
            "partner_sku": sku,
            "price_currency": "PEN",
            "price": Decimal(precio),
            "num_in_stock": stock,
        },
    )

# 8. Envío solo para productos físicos
OrderAndItemCharges.objects.get_or_create(
    name="Envío Delivery Local / Nacional",
    defaults={
        "description": "Entrega estándar en 24 a 48 horas",
        "price_per_order": Decimal("10.00"),
        "price_per_item": Decimal("0.00"),
        "free_shipping_threshold": Decimal("150.00"),
    },
)

print("¡BARBERÍA FERCHO ACTUALIZADA CON CORTES Y PRODUCTOS!")
import os
from decimal import Decimal
import mercadopago
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View
from oscar.apps.checkout.mixins import OrderPlacementMixin
from oscar.core.loading import get_class, get_model

CheckoutSessionData = get_class('checkout.utils', 'CheckoutSessionData')
OrderTotalCalculator = get_class('checkout.calculators', 'OrderTotalCalculator')
ShippingRepository = get_class('shipping.repository', 'Repository')
ShippingAddress = get_model('order', 'ShippingAddress')
UserAddress = get_model('address', 'UserAddress')
SourceType = get_model('payment', 'SourceType')
Source = get_model('payment', 'Source')


def _obtener_shipping_address(request, session_data):
    """Obtiene la dirección de envío desde la sesión de Oscar (nueva o guardada)."""
    if hasattr(session_data, 'new_shipping_address_fields'):
        addr_fields = session_data.new_shipping_address_fields()
        if addr_fields:
            return ShippingAddress(**addr_fields)

    if hasattr(session_data, 'shipping_user_address_id'):
        addr_id = session_data.shipping_user_address_id()
        if addr_id:
            try:
                user_addr = UserAddress.objects.get(pk=addr_id)
                shipping_addr = ShippingAddress()
                user_addr.populate_alternative_model(shipping_addr)
                return shipping_addr
            except UserAddress.DoesNotExist:
                pass
    return None


def _calcular_total_y_monto_cobrar(request, tipo_pago):
    basket = request.basket
    session_data = CheckoutSessionData(request)
    shipping_address = _obtener_shipping_address(request, session_data)

    methods = ShippingRepository().get_shipping_methods(
        basket=basket,
        user=request.user if request.user.is_authenticated else None,
        shipping_addr=shipping_address,
        request=request,
    )

    method_code = session_data.shipping_method_code(basket) if hasattr(session_data, 'shipping_method_code') else None
    shipping_method = next((m for m in methods if m.code == method_code), methods[0] if methods else None)

    shipping_charge = shipping_method.calculate(basket) if shipping_method else None
    order_total = OrderTotalCalculator().calculate(basket, shipping_charge)
    total_pen = order_total.incl_tax

    # Si elige adelanto en barbería, cobramos exactamente el 50%
    if tipo_pago == 'adelanto_50':
        monto_cobrar = (total_pen * Decimal('0.50')).quantize(Decimal('0.01'))
        titulo = f"Adelanto 50% Reserva - Barbería Fercho (Total: S/ {total_pen:.2f})"
    else:
        monto_cobrar = total_pen.quantize(Decimal('0.01'))
        titulo = "Pedido Online - Barbería Fercho"

    return order_total, shipping_method, shipping_charge, shipping_address, monto_cobrar, titulo


def crear_preferencia_mp(request):
    """Genera el enlace de pago en Mercado Pago (100% o 50% adelanto)."""
    if not request.basket or request.basket.is_empty:
        return JsonResponse({'error': 'Tu carrito está vacío.'}, status=400)

    access_token = os.environ.get('MP_ACCESS_TOKEN', '').strip()
    if not access_token:
        return JsonResponse({'error': 'Falta MP_ACCESS_TOKEN en .env.local'}, status=500)

    tipo_pago = request.POST.get('tipo_pago', 'total_100')
    request.session['fercho_tipo_pago'] = tipo_pago

    _, _, _, _, monto_cobrar, titulo = _calcular_total_y_monto_cobrar(request, tipo_pago)

    sdk = mercadopago.SDK(access_token)
    base_url = request.build_absolute_uri('/').rstrip('/')

    preference_data = {
        "items": [
            {
                "title": titulo,
                "quantity": 1,
                "unit_price": float(monto_cobrar),
                "currency_id": "PEN",
            }
        ],
        "back_urls": {
            "success": f"{base_url}{reverse('mp_retorno')}",
            "failure": f"{base_url}{reverse('checkout:preview')}",
            "pending": f"{base_url}{reverse('mp_retorno')}",
        },
        "statement_descriptor": "BARBERIA FERCHO",
    }

    response = sdk.preference().create(preference_data)
    pref = response.get("response", {})

    init_point = (
        pref.get("sandbox_init_point")
        if access_token.startswith("TEST-")
        else pref.get("init_point")
    )

    if not init_point:
        return JsonResponse({
            'error': 'No se pudo iniciar Mercado Pago.',
            'token_leido': f"{access_token[:12]}... (largo: {len(access_token)})",
            'detalle': pref
        }, status=400)

    return redirect(init_point)


class MercadoPagoRetornoView(OrderPlacementMixin, View):
    """Recibe al cliente cuando Mercado Pago aprueba el cobro y registra la orden en Oscar."""

    def dispatch(self, request, *args, **kwargs):
        status = request.GET.get('status') or request.GET.get('collection_status')
        payment_id = request.GET.get('payment_id') or request.GET.get('collection_id')

        if status != 'approved' or not payment_id:
            return redirect('checkout:preview')

        sdk = mercadopago.SDK(os.environ.get('MP_ACCESS_TOKEN', '').strip())
        payment_info = sdk.payment().get(payment_id).get("response", {})
        if payment_info.get("status") != "approved":
            return redirect('checkout:preview')

        monto_pagado = Decimal(str(payment_info.get("transaction_amount", "0.00")))
        tipo_pago = request.session.get('fercho_tipo_pago', 'total_100')

        basket = request.basket
        if not basket or basket.is_empty:
            return redirect('checkout:thank-you')

        session_data = CheckoutSessionData(request)
        order_total, shipping_method, shipping_charge, shipping_address, _, _ = _calcular_total_y_monto_cobrar(
            request, tipo_pago
        )

        etiqueta = (
            "Mercado Pago (Adelanto 50% Pagado)"
            if tipo_pago == 'adelanto_50'
            else "Mercado Pago (100% Pagado)"
        )
        source_type, _ = SourceType.objects.get_or_create(name=etiqueta)
        source = Source(
            source_type=source_type,
            currency='PEN',
            amount_allocated=monto_pagado,
            amount_debited=monto_pagado,
            reference=str(payment_id),
        )
        self.add_payment_source(source)
        self.add_payment_event('Paid', monto_pagado, reference=str(payment_id))

        order_number = self.generate_order_number(basket)
        billing_address = self.get_billing_address(shipping_address)

        self.handle_order_placement(
            order_number=order_number,
            user=request.user,
            basket=basket,
            shipping_address=shipping_address,
            shipping_method=shipping_method,
            shipping_charge=shipping_charge,
            billing_address=billing_address,
            order_total=order_total,
            guest_email=session_data.get_guest_email(),
        )
        return redirect('checkout:thank-you')
import stripe
from decimal import Decimal
from django.conf import settings
from django.shortcuts import render, redirect, reverse, get_object_or_404
from orders.models import Order

# Stripe 인스턴스 생성
stripe.api_key = settings.STRIPE_SECRET_KEY
stripe.api_version = settings.STRIPE_API_VERSION

def payment_process(request):
    order_id = request.session.get('order_id', None)
    order = get_object_or_404(Order, id=order_id)

    if request.method == 'POST':
        success_url = request.build_absolute_uri(reverse('payment:completed'))
        cancel_url = request.build_absolute_uri(reverse('payment:canceled'))
        # Stripe 결제 세션 데이터
        session_data = {
            'mode':'payment',
            'client_reference_id':order.id,
            'success_url':success_url,
            'cancel_url':cancel_url,
            'line_items':[],
        }

        # Stripe 결제 세션에 주문 품목 추가
        for item in order.items.all():
            session_data['line_items'].append({
                'price_data':{
                    'unit_amount':int(item.price * Decimal('100')),
                    'currency':'usd',
                    'product_data':{
                        'name':item.product.name,
                    },
                },
                'quantity':item.quantity,
            })

        # Stripe 쿠폰
        if order.coupon:
            stripe_coupon = stripe.Coupon.create(name=order.coupon.code,
                                                 percent_off=order.discount,
                                                 duration='once')
            session_data['discounts'] = [{'coupon':stripe_coupon.id}]

        # Stripe 결제 세션 생성
        session = stripe.checkout.Session.create(**session_data)

        # Stripe 결제 양식으로 리다이렉션
        return redirect(session.url, code=303)
    else:
        return render(request, 'payment/process.html', locals())

def payment_completed(request):
    return render(request, 'payment/completed.html')

def payment_canceled(request):
    return render(request, 'payment/canceled.html')

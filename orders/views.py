import weasyprint
from django.conf import settings
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from cart.cart import Cart

from .models import OrderItem, Order
from .forms import OrderCreateForm
from .tasks import order_created

# 새로운 주문을 생성
def order_create(request):
    # 세션으로부터 현재 카트를 가져옴
    cart = Cart(request)

    # POST 요청
    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        
        # 전송된 데이터의 유효성 검사
        if form.is_valid():
            # 데이터가 유효하면 데이터베이스에 새로운 주문을 생성
            order = form.save(commit=False)
            
            # 카트에 쿠폰이 포함된 경우, 관련 쿠폰과 적용된 할인을 저장
            if cart.coupon:
                order.coupon = cart.coupon
                order.discount = cart.coupon.discount

            order.save()
            
            # 카트의 item들을 반복해서 각 아이템에 대한 OrderItem을 생성
            for item in cart:
                OrderItem.objects.create(order=order, product=item['product'],
                                         price=item['price'], quantity=item['quantity'])

            # 카트의 콘텐츠를 비우기
            cart.clear()
            # 비동기 작업 실행
            order_created.delay(order.id)
            # 세션 순서 결정
            request.session['order_id'] = order.id
            # 결제 리다이렉션
            return redirect(reverse('payment:process'))
    # GET 요청
    else:
        # OrderCreateForm 폼을 인스턴스화하고 create.html 템플릿을 렌더링
        form = OrderCreateForm()

    return render(request, 'orders/order/create.html',
                  {'cart':cart, 'form':form})

@staff_member_required
def admin_order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    return render(request, 'admin/orders/order/detail.html',
                  {'order':order})

@staff_member_required
def admin_order_pdf(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    html = render_to_string('orders/order/pdf.html', {'order':order})
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'filename=order_{order.id}.pdf'
    weasyprint.HTML(string=html).write_pdf(response, stylesheets=[weasyprint.CSS(settings.STATIC_ROOT / 'css/pdf.css')])

    return response
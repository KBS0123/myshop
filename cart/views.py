from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from shop.models import Product
from shop.recommender import Recommender
from coupons.forms import CouponApplyForm

from .cart import Cart
from .forms import CartAddProductForm

# 카트에 제품을 추가하거나 기존 제품의 수량을 업데이트
@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    form = CartAddProductForm(request.POST)

    # product_id로 Product 인스턴스를 조회하고 CartAddProductForm의 유효성 검사
    # 폼이 유효하면 카트에 제품을 추가하거나 업데이트
    if form.is_valid():
        cd = form.cleaned_data
        cart.add(product=product, quantity=cd['quantity'], override_quantity=cd['override'])

    return redirect('cart:cart_detail')

# 카트에서 품목을 제거
@require_POST
def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    # product_id로 Product 인스턴스를 조회하고 카트에서 제품을 제거
    cart.remove(product)

    return redirect('cart:cart_detail')

# 현재 카트와 카트의 아이템들을 표시
def cart_detail(request):
    cart = Cart(request)

    # 사용자가 카트 상세 페이지에서 수량을 변경할 수 있도록 허용
    # 현재 item의 수량으로 폼을 초기화하고 override 필드를 True로 설정하여
    # 폼을 cart_add뷰에 제출할 때 현재 수량이 새로운 수량으로 변경
    for item in cart:
        item['update_quantity_form'] = CartAddProductForm(
                                        initial={
                                            'quantity':item['quantity'],
                                            'override':True
                                        })

    coupon_apply_form = CouponApplyForm()
    r = Recommender()
    cart_products = [item['product'] for item in cart]

    if cart_products:
        recommended_products = r.suggest_products_for(cart_products, max_results=4)
    else:
        recommended_products = []

    return render(request, 'cart/detail.html',
                  {'cart':cart,
                          'coupon_apply_form':coupon_apply_form,
                          'recommended_products':recommended_products})
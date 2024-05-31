from decimal import Decimal
from django.conf import settings

from shop.models import Product
from coupons.models import Coupon

class Cart:
    # 카트를 초기화 (생성자)
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)

        if not cart:
            # 세션에 빈 카트 저장
            cart = self.session[settings.CART_SESSION_ID] = {}

        self.cart = cart
        # 현재 적용된 쿠폰 저장
        self.coupon_id = self.session.get('coupon_id')

    # 카트에 제품을 추가 또는 수량 업데이트
    def add(self, product, quantity=1, override_quantity=False):
        product_id = str(product.id)

        if product_id not in self.cart:
            self.cart[product_id] = {'quantity':0, 'price':str(product.price)}

        if override_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity

        self.save()

    # 세션을 "modified"로 표시하여 저장되도록 함
    def save(self):
        self.session.modified = True

    # 카트에서 제품 제거
    def remove(self, product):
        product_id = str(product.id)

        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    # 카트에 있는 item을 반복하고 DB에서 제품을 가져옴
    def __iter__(self):
        product_ids = self.cart.keys()
        # Product 객체를 가져와 카트에 추가
        products = Product.objects.filter(id__in=product_ids)
        cart = self.cart.copy()

        for product in products:
            cart[str(product.id)]['product'] = product

        for item in cart.values():
            item['price'] = Decimal(item['price'])
            item['total_price'] = item['price'] * item['quantity']
            yield item

    # 모든 카트 item들의 수량의 합을 반환
    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())

    # 카트에 있는 item의 총 가격을 계산
    def get_total_price(self):
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())

    # 카트 세션 삭제
    def clear(self):
        del self.session[settings.CART_SESSION_ID]
        self.save()

    @property
    def coupon(self):
        # 카트에 coupon_id 속성이 포함된 경우 지정된 ID를 가진 Coupon 객체가 반환
        if self.coupon_id:
            try:
                return Coupon.objects.get(id=self.coupon_id)
            except Coupon.DoesNotExist:
                pass

        return None

    def get_discount(self):
        # 카트에 쿠폰이 포함된 경우
        # 해당 쿠폰의 할인율을 검색하고 총 금액에서 차감할 금액을 반환
        if self.coupon:
            return (self.coupon.discount / Decimal(100) * self.get_total_price())

        return Decimal(0)

    def get_total_price_after_discount(self):
        # get_discount 메서드에서 반환된 금액을 공제 후 카트의 총 금액 반환
        return self.get_total_price() - self.get_discount()
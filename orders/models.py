from decimal import Decimal
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _

from shop.models import Product
from coupons.models import Coupon

# 고객 정보를 저장하는 여러 필드
# 이 필드를 사용하여 결제 주문과 미결제 주문을 구분
class Order(models.Model):
    first_name = models.CharField(_('first_name'), max_length=50)
    last_name = models.CharField(_('last_name'), max_length=50)
    email = models.EmailField(_('email'))
    address = models.CharField(_('address'), max_length=250)
    postal_code = models.CharField(_('postal_code'), max_length=20)
    city = models.CharField(_('city'), max_length=100)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    paid = models.BooleanField(default=False)
    stripe_id = models.CharField(max_length=250, blank=True)
    coupon = models.ForeignKey(Coupon, related_name='orders', null=True,
                               blank=True, on_delete=models.SET_NULL)
    discount = models.IntegerField(default=0,
                                   validators=[MinValueValidator(0), MaxValueValidator(100)])

    class Meta:
        ordering = ['-created']
        indexes = [models.Index(fields=['-created'])]

    def __str__(self):
        return f'Order {self.id}'

    # 구매한 품목의 총 비용을 반환
    def get_total_cost(self):
        total_cost = self.get_total_cost_before_discount()
        return total_cost - self.get_discount()

    def get_stripe_url(self):
        if not self.stripe_id:
            # 연결된 결제 없음
            return ''

        if '_test_' in settings.STRIPE_SECRET_KEY:
            # 테스트 결제를 위한 Stripe 경로
            path = '/test/'
        else:
            # 실제 결제를 위한 Stripe 경로
            path = '/'

        return f'https://dashboard.stripe.com{path}payments/{self.stripe_id}'

    def get_total_cost_before_discount(self):
        return sum(item.get_cost() for item in self.items.all())

    def get_discount(self):
        total_cost = self.get_total_cost_before_discount()

        if self.discount:
            return total_cost * (self.discount / Decimal(100))

        return Decimal(0)

# 각 item에 대한 결제한 제품, 수량, 가격을 저장
class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='order_items', on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return str(self.id)

    # 품목 가격에 수량을 곱하여 비용을 반환
    def get_cost(self):
        return self.price * self.quantity
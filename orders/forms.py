from django import forms

from .models import Order

# 새로운 Order 객체를 만드는 데 사용
class OrderCreateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['first_name', 'last_name', 'email', 'address', 'postal_code', 'city']

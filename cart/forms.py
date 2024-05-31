from django import forms
from django.utils.translation import gettext_lazy as _

PRODUCT_QUANTITY_CHOICES = [(i, str(i)) for i in range(1, 21)]

class CartAddProductForm(forms.Form):
    # 사용자가 1~20 사이의 수량을 선택할 수 있게 함
    # coerce=int를 사용하여 입력값을 정수로 변환
    quantity = forms.TypedChoiceField(choices=PRODUCT_QUANTITY_CHOICES,
                                      coerce=int, label=_('Quantity'))
    # 카트에 있는 기존 수량에 주어진 수량을 추가(거짓)할지 기존 수량을 주어진 수량으로 덮어 쓸지(참) 표시
    # HiddenInput 위젯을 사용하여 사용자에게 표시되지 않음
    override = forms.BooleanField(required=False, initial=False,
                                  widget=forms.HiddenInput)

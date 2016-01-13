from __future__ import unicode_literals

from django import forms

from thorbanks.forms import PaymentFormMixin

from shop.models import Order


class AuthForm(PaymentFormMixin, forms.Form):
    bank_name = PaymentFormMixin.get_bank_name_field()


class OrderForm(PaymentFormMixin, forms.ModelForm):
    class Meta:
        model = Order
        fields = ['amount']

    bank_name = PaymentFormMixin.get_bank_name_field()

from __future__ import unicode_literals

from warnings import warn

from django import forms
from django.conf import settings as django_settings
from django.forms.widgets import RadioFieldRenderer
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils.encoding import force_text
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from thorbanks import settings
from thorbanks.settings import get_send_ref
from thorbanks.utils import create_signature, nordea_generate_mac
from thorbanks.signals import transaction_started
from thorbanks.utils import calculate_731_checksum


class AuthRequestBase(forms.Form):
    def __init__(self, bank_name, redirect_to, response_url, *args, **kwargs):
        self.auth = settings.get_model('Authentication')()
        self.auth.bank_name = bank_name
        self.auth.redirect_after_success = redirect_to
        self.auth.redirect_on_failure = redirect_to
        self.auth.save()

        initial = self.prepare(bank_name, redirect_to, response_url, *args, **kwargs)

        super(AuthRequestBase, self).__init__(initial, *args, **kwargs)

        if not self.is_valid():
            raise RuntimeError("invalid initial data")  # pragma no cover

        self.finalize()
        if not self.is_valid():
            raise RuntimeError("signature is invalid")  # pragma no cover

    def prepare(self, *args, **kwargs):
        raise NotImplementedError  # pragma no cover

    def finalize(self):
        raise NotImplementedError  # pragma no cover

    def redirect_html(self):
        """ Redirection html """
        html = '<form action="%s" method="POST" id="banklink_redirect_url" accept-charset="%s">' % (
            self.get_request_url(), self.get_encoding())

        for field in self:
            html += force_text(field) + "\n"

        html += '</form>'
        html += """<script type="text/javascript">
                       document.forms['banklink_redirect_url'].submit();
                   </script>
                """

        return mark_safe(html)

    def get_request_url(self):
        return settings.get_request_url(self.auth.bank_name)

    def get_encoding(self):
        return 'UTF-8'


class IPizzaAuthRequest(AuthRequestBase):
    VK_SERVICE = forms.CharField(widget=forms.HiddenInput())
    VK_VERSION = forms.CharField(widget=forms.HiddenInput())
    VK_SND_ID = forms.CharField(widget=forms.HiddenInput())
    VK_REC_ID = forms.CharField(widget=forms.HiddenInput())
    VK_NONCE = forms.CharField(widget=forms.HiddenInput(), max_length=50)
    VK_RETURN = forms.CharField(widget=forms.HiddenInput())
    VK_DATETIME = forms.CharField(widget=forms.HiddenInput())

    VK_ENCODING = forms.CharField(widget=forms.HiddenInput())

    VK_RID = forms.CharField(widget=forms.HiddenInput(), required=False)
    VK_MAC = forms.CharField(widget=forms.HiddenInput(), required=False)

    def prepare(self, bank_name, redirect_to, response_url, *args, **kwargs):
        initial = {
            'VK_SERVICE': '4012',
            'VK_VERSION': '008',
            'VK_SND_ID': settings.get_client_id(bank_name),
            'VK_REC_ID': settings.get_bank_id(bank_name),
            'VK_NONCE': self.auth.pk,
            'VK_RETURN': response_url,
            'VK_DATETIME': self.auth.created.strftime('%Y-%m-%dT%H:%M:%S%z'),
            'VK_RID': '',
            'VK_REPLY': '3013',
            'VK_ENCODING': self.get_encoding(),
        }
        return initial

    def finalize(self):
        mac = create_signature(self.cleaned_data, self.auth.bank_name, auth=True)
        self.data['VK_MAC'] = mac


class NordeaAuthRequest(AuthRequestBase):
    A01Y_ACTION_ID = forms.CharField(widget=forms.HiddenInput())
    A01Y_VERS = forms.CharField(widget=forms.HiddenInput())
    A01Y_RCVID = forms.CharField(widget=forms.HiddenInput())
    A01Y_LANGCODE = forms.CharField(widget=forms.HiddenInput())
    A01Y_STAMP = forms.CharField(widget=forms.HiddenInput())
    A01Y_IDTYPE = forms.CharField(widget=forms.HiddenInput())
    A01Y_RETLINK = forms.CharField(widget=forms.HiddenInput())
    A01Y_CANLINK = forms.CharField(widget=forms.HiddenInput())
    A01Y_REJLINK = forms.CharField(widget=forms.HiddenInput())
    A01Y_KEYVERS = forms.CharField(widget=forms.HiddenInput())
    A01Y_ALG = forms.CharField(widget=forms.HiddenInput())
    A01Y_MAC = forms.CharField(widget=forms.HiddenInput(), required=False)

    def prepare(self, bank_name, redirect_to, response_url, *args, **kwargs):
        initial = {
            'A01Y_ACTION_ID': '701',
            'A01Y_VERS': '0002',
            'A01Y_RCVID': settings.get_client_id(bank_name),
            'A01Y_LANGCODE': 'ET',
            'A01Y_STAMP': self.auth.pk,
            'A01Y_IDTYPE': '02',
            'A01Y_RETLINK': response_url,
            'A01Y_CANLINK': response_url,
            'A01Y_REJLINK': response_url,
            'A01Y_KEYVERS': '0001',     # TODO: support multiple keys
            'A01Y_ALG': '01',           # We use MD5 to calculate MAC since nordea LIVE does not like SHA1
        }
        return initial

    def finalize(self):
        mac_token_fields = (
            'A01Y_ACTION_ID',
            'A01Y_VERS',
            'A01Y_RCVID',
            'A01Y_LANGCODE',
            'A01Y_STAMP',
            'A01Y_IDTYPE',
            'A01Y_RETLINK',
            'A01Y_CANLINK',
            'A01Y_REJLINK',
            'A01Y_KEYVERS',
            'A01Y_ALG',
        )
        link_config = settings.LINKS[self.auth.bank_name]
        mac_key = link_config['MAC_KEY']
        mac = nordea_generate_mac(self.cleaned_data, mac_token_fields, mac_key)

        self.data['A01Y_MAC'] = mac


class PaymentRequestBase(forms.Form):
    def __init__(self, *args, **kwargs):
        self.transaction = settings.get_model('Transaction')()
        self.transaction.bank_name = kwargs['bank_name']
        self.transaction.description = kwargs['message']
        self.transaction.amount = round(kwargs['amount'], 2)
        self.transaction.currency = kwargs['currency']
        self.transaction.message = kwargs['message']

        self.transaction.redirect_after_success = kwargs['redirect_to']
        self.transaction.redirect_on_failure = kwargs['redirect_on_failure']
        self.transaction.save()

        transaction_started.send(settings.get_model('Transaction'), transaction=self.transaction)

        initial = self.prepare(self.transaction, kwargs['url'])

        super(PaymentRequestBase, self).__init__(initial, *args)

        if not self.is_valid():
            raise RuntimeError("invalid initial data")

        self.finalize()
        if not self.is_valid():
            raise RuntimeError("signature is invalid")

    @classmethod
    def prepare(cls, transaction, url, language='EST'):
        raise NotImplementedError

    def finalize(self):
        raise NotImplementedError

    def redirect_html(self):
        html = '<form action="%s" method="POST" id="banklink_redirect_url" accept-charset="%s">' % (
            self.get_request_url(), self.get_encoding())
        for field in self:
            html += force_text(field) + u"\n"
        html += '</form>'
        html += '''<script type="text/javascript">
                    document.forms['banklink_redirect_url'].submit();
                    </script>'''
        return mark_safe(html)

    def submit_button(self, value=u"Make the payment"):
        html = '<form action="%s" method="POST">' % (settings.get_request_url(self.transaction.bank_name))
        for field in self:
            html += force_text(field) + u"\n"
        html += '<input type="submit" value="%s" />' % value
        html += '</form>'
        return mark_safe(html)

    def as_html(self, with_submit=False, id="banklink_payment_form", submit_value="submit"):
        warn("deprecated", DeprecationWarning)
        html = '<form action="%s" method="POST" id="%s">' % (settings.get_request_url(self.transaction.bank_name), id)
        for field in self:
            html += force_text(field) + u"\n"
        if with_submit:
            html += '<input type="submit" value="%s"/>' % (submit_value, )
        html += '</form>'
        return html

    def get_request_url(self):
        return settings.get_request_url(self.transaction.bank_name)

    def get_encoding(self):
        return 'UTF-8'

    def get_redirect_response_html(self):
        return render_to_string("thorbanks/request.html", {'form': self})

    def get_redirect_response(self):
        return HttpResponse(self.get_redirect_response_html())


class PaymentRequest(PaymentRequestBase):
    """ Creates payment request and Transaction object.

    It also acts as a facade through which transaction object and HTTP redirect can be retrieved.
    """
    VK_SERVICE = forms.CharField(widget=forms.HiddenInput())
    VK_VERSION = forms.CharField(widget=forms.HiddenInput())
    VK_SND_ID = forms.CharField(widget=forms.HiddenInput())
    VK_STAMP = forms.CharField(widget=forms.HiddenInput())
    VK_AMOUNT = forms.CharField(widget=forms.HiddenInput())
    VK_CURR = forms.CharField(widget=forms.HiddenInput())
    VK_REF = forms.CharField(widget=forms.HiddenInput(), required=False)
    VK_MSG = forms.CharField(widget=forms.HiddenInput())
    VK_RETURN = forms.CharField(widget=forms.HiddenInput())
    VK_CANCEL = forms.CharField(widget=forms.HiddenInput())
    VK_DATETIME = forms.CharField(widget=forms.HiddenInput())
    VK_MAC = forms.CharField(widget=forms.HiddenInput(), required=False)
    VK_LANG = forms.CharField(widget=forms.HiddenInput())
    VK_ENCODING = forms.CharField(widget=forms.HiddenInput())

    @classmethod
    def prepare(cls, transaction, url, language='EST'):
        assert language in ['EST', 'ENG', 'RUS']

        return {
            'VK_SERVICE': '1012',
            'VK_VERSION': '008',
            'VK_ENCODING': 'UTF-8',

            'VK_DATETIME': transaction.created.strftime('%Y-%m-%dT%H:%M:%S%z'),
            'VK_RETURN': url,
            'VK_CANCEL': url,
            'VK_LANG': language,
            'VK_SND_ID': settings.get_client_id(transaction.bank_name),

            'VK_STAMP': transaction.pk,
            'VK_REF': calculate_731_checksum(transaction.pk) if get_send_ref(transaction.bank_name) else '',

            'VK_AMOUNT': transaction.amount,
            'VK_CURR': transaction.currency,
            'VK_MSG': transaction.message,
        }

    def finalize(self):
        self.data['VK_MAC'] = create_signature(self.cleaned_data, self.transaction.bank_name)


class PaymentFormMixin(object):
    """
    Base form mixin that lets the user choose the bank used for payment.
    Note that you MUST add bank_name field to your form class, you can use `get_bank_name_field()` method to get a field
    object for that. E.g.

    ```
    class OrderForm(PaymentFormMixin, forms.Form):
        bank_name = PaymentFormMixin.get_bank_name_field()
        # Add your custom fields and/or inherit from ModelForm instead of Form
    ```
    """
    class BankNameFieldRenderer(RadioFieldRenderer):
        """ Augmented RadioFieldRenderer that lets us use out own CSS class.
        """
        UL_HTML = '<ul class="payment-options clearfix">%s</ul>'
        LI_HTML = '<li>%s</li>'

        def field_render(self, field):
            if 'id' in field.attrs:
                label_for = ' for="%s_%s"' % (field.attrs['id'], field.index)
            else:
                label_for = ''
            choice_label = conditional_escape(force_text(field.choice_label))

            return mark_safe('%s <label%s>%s</label>' % (field.tag(), label_for, choice_label))

        def render(self):
            return mark_safe(self.UL_HTML % '\n'.join(
                [self.LI_HTML % force_text(self.field_render(w)) for w in self]))

    def __init__(self, *args, **kwargs):
        self.banklink_order_overwrite = kwargs.pop('banklink_order_overwrite', dict())
        # None means all banks in the settings are permitted
        payment_methods = kwargs.pop('payment_methods', None)

        super(PaymentFormMixin, self).__init__(*args, **kwargs)

        if not self.fields['bank_name'].required:
            raise NotImplementedError('bank_name field must be required')

        self.fields['bank_name'].choices = self.get_payment_method_choices(payment_methods)
        self.fields['bank_name'].error_messages['required'] = _('You have to select a method of payment.')

    @classmethod
    def get_bank_name_field(cls):
        return forms.ChoiceField(label='', required=True,
                                 widget=forms.RadioSelect(renderer=cls.BankNameFieldRenderer))

    def get_payment_method_choices(self, all_payment_methods):
        payment_choices = []
        label_pattern = """<img alt="%s" src="%s" />"""

        for bank_id, bank_name, image_name, order in settings.get_bank_choices():
            if self.banklink_order_overwrite and bank_id in self.banklink_order_overwrite:
                order = self.banklink_order_overwrite[bank_id]

            if all_payment_methods is None or bank_id in all_payment_methods:
                label = label_pattern % (bank_name, self.get_bank_image_path(image_name))
                payment_choices.append((bank_id, mark_safe(label), order))

        return [(y[0], y[1]) for y in sorted(payment_choices, key=lambda x: x[2])]

    def get_bank_image_path(self, image_name):
        logos_dir = getattr(django_settings, 'BANKLINK_LOGO_PATH', 'img/payment/')
        return '%s%s%s' % (django_settings.STATIC_URL, logos_dir, image_name)

    def get_bank_id(self):
        if not self.cleaned_data:
            return None

        return self.cleaned_data['bank_name']

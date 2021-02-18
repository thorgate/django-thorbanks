from django import forms
from django.conf import settings as django_settings
from django.forms.widgets import RadioSelect
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils.encoding import force_str
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from thorbanks import settings
from thorbanks.settings import get_send_ref
from thorbanks.signals import transaction_started
from thorbanks.utils import calculate_731_checksum, create_signature


class AuthRequestBase(forms.Form):
    def __init__(
        self, bank_name, redirect_to, response_url, *args, extra_fields=None, **kwargs
    ):
        self.auth = settings.get_model("Authentication")()
        self.auth.bank_name = bank_name
        self.auth.redirect_after_success = redirect_to
        self.auth.redirect_on_failure = redirect_to

        if extra_fields is not None:
            for key, value in extra_fields.items():
                setattr(self.auth, key, value)

        self.auth.save()

        initial = self.prepare(bank_name, redirect_to, response_url, *args, **kwargs)

        super(AuthRequestBase, self).__init__(initial, *args, **kwargs)

        if not self.is_valid():
            raise RuntimeError("invalid initial data")  # pragma no cover

        self.finalize()
        if not self.is_valid():
            raise RuntimeError("signature is invalid")  # pragma no cover

    def prepare(self, bank_name, redirect_to, response_url, *args, **kwargs):
        raise NotImplementedError  # pragma no cover

    def finalize(self):
        raise NotImplementedError  # pragma no cover

    def redirect_html(self):
        """ Redirection html """
        html = (
            '<form action="%s" method="POST" id="banklink_redirect_url" accept-charset="%s">'
            % (self.get_request_url(), self.get_encoding())
        )

        for field in self:
            html += force_str(field) + "\n"

        html += "</form>"
        html += """<script type="text/javascript">
                       document.forms['banklink_redirect_url'].submit();
                   </script>
                """

        return mark_safe(html)

    def get_request_url(self):
        return settings.get_request_url(self.auth.bank_name)

    def get_encoding(self):
        return "UTF-8"

    def get_redirect_response_html(self):
        return render_to_string("thorbanks/auth-request.html", {"form": self})

    def get_redirect_response(self):
        return HttpResponse(self.get_redirect_response_html(), content_type="text/html")


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
            "VK_SERVICE": "4012",
            "VK_VERSION": "008",
            "VK_SND_ID": settings.get_client_id(bank_name),
            "VK_REC_ID": settings.get_bank_id(bank_name),
            "VK_NONCE": self.auth.pk,
            "VK_RETURN": response_url,
            "VK_DATETIME": self.auth.created.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "VK_RID": "",
            "VK_REPLY": "3013",
            "VK_ENCODING": self.get_encoding(),
        }
        return initial

    def finalize(self):
        mac = create_signature(self.cleaned_data, self.auth.bank_name, auth=True)
        self.data["VK_MAC"] = mac


class PaymentRequestBase(forms.Form):
    def __init__(self, *args, extra_fields=None, **kwargs):
        if "existing_transaction" in kwargs:
            self.transaction = kwargs.pop("existing_transaction")

        else:
            self.transaction = settings.get_model("Transaction")()
            self.transaction.bank_name = kwargs["bank_name"]
            self.transaction.description = kwargs["message"]
            self.transaction.amount = round(kwargs["amount"], 2)
            self.transaction.currency = kwargs["currency"]
            self.transaction.message = kwargs["message"]

            self.transaction.redirect_after_success = kwargs["redirect_to"]
            self.transaction.redirect_on_failure = kwargs["redirect_on_failure"]

            if extra_fields is not None:
                for key, value in extra_fields.items():
                    setattr(self.transaction, key, value)

            self.transaction.save()

            transaction_started.send(
                settings.get_model("Transaction"), transaction=self.transaction
            )

        initial = self.prepare(self.transaction, kwargs["url"])

        super(PaymentRequestBase, self).__init__(initial, *args)

        if not self.is_valid():
            raise RuntimeError("invalid initial data")

        self.finalize()
        if not self.is_valid():
            raise RuntimeError("signature is invalid")

    def prepare(self, transaction, url, language="EST"):
        raise NotImplementedError

    def finalize(self):
        raise NotImplementedError

    def redirect_html(self):
        html = (
            '<form action="%s" method="POST" id="banklink_redirect_url" accept-charset="%s">'
            % (self.get_request_url(), self.get_encoding())
        )
        for field in self:
            html += force_str(field) + "\n"
        html += "</form>"
        html += """<script type="text/javascript">
                    document.forms['banklink_redirect_url'].submit();
                    </script>"""
        return mark_safe(html)

    def submit_button(self, value="Make the payment"):
        html = '<form action="%s" method="POST">' % (
            settings.get_request_url(self.transaction.bank_name)
        )
        for field in self:
            html += force_str(field) + "\n"
        html += '<input type="submit" value="%s" />' % value
        html += "</form>"
        return mark_safe(html)

    def get_request_url(self):
        return settings.get_request_url(self.transaction.bank_name)

    def get_encoding(self):
        return "UTF-8"

    def get_redirect_response_html(self):
        return render_to_string("thorbanks/payment-request.html", {"form": self})

    def get_redirect_response(self):
        return HttpResponse(self.get_redirect_response_html(), content_type="text/html")


class PaymentRequest(PaymentRequestBase):
    """Creates payment request and Transaction object.

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

    def prepare(self, transaction, url, language="EST"):
        assert language in ["EST", "ENG", "RUS"]

        return {
            "VK_SERVICE": "1012",
            "VK_VERSION": "008",
            "VK_ENCODING": self.get_encoding(),
            "VK_DATETIME": transaction.created.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "VK_RETURN": url,
            "VK_CANCEL": url,
            "VK_LANG": language,
            "VK_SND_ID": settings.get_client_id(transaction.bank_name),
            "VK_STAMP": transaction.pk,
            "VK_REF": calculate_731_checksum(transaction.pk)
            if get_send_ref(transaction.bank_name)
            else "",
            "VK_AMOUNT": transaction.amount,
            "VK_CURR": transaction.currency,
            "VK_MSG": transaction.message,
        }

    def finalize(self):
        self.data["VK_MAC"] = create_signature(
            self.cleaned_data, self.transaction.bank_name
        )


class PaymentFormMixin:
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

    class BankNameFieldWidget(RadioSelect):
        """Augmented RadioSelect that lets us use our own CSS class."""

        template_name = "thorbanks/payment_widget.html"
        option_template_name = "thorbanks/input_option.html"

    def __init__(self, *args, **kwargs):
        self.banklink_order_overwrite = kwargs.pop("banklink_order_overwrite", dict())
        # None means all banks in the settings are permitted
        payment_methods = kwargs.pop("payment_methods", None)

        super(PaymentFormMixin, self).__init__(*args, **kwargs)

        if not self.fields["bank_name"].required:
            raise NotImplementedError("bank_name field must be required")

        self.fields["bank_name"].choices = self.get_payment_method_choices(
            payment_methods
        )
        self.fields["bank_name"].error_messages["required"] = _(
            "You have to select a method of payment."
        )

    @classmethod
    def get_bank_name_field(cls):
        return forms.ChoiceField(
            label="Bank name", required=True, widget=cls.BankNameFieldWidget()
        )

    def get_payment_method_choices(self, all_payment_methods):
        payment_choices = []
        label_pattern = """<img alt="%s" src="%s" />"""

        for bank_id, bank_name, image_name, order in settings.get_bank_choices():
            if (
                self.banklink_order_overwrite
                and bank_id in self.banklink_order_overwrite
            ):
                order = self.banklink_order_overwrite[bank_id]

            if all_payment_methods is None or bank_id in all_payment_methods:
                label = label_pattern % (
                    bank_name,
                    self.get_bank_image_path(image_name),
                )
                payment_choices.append((bank_id, mark_safe(label), order))

        return [(y[0], y[1]) for y in sorted(payment_choices, key=lambda x: x[2])]

    def get_bank_image_path(self, image_name):
        logos_dir = getattr(django_settings, "BANKLINK_LOGO_PATH", "img/payment/")
        return "%s%s%s" % (django_settings.STATIC_URL, logos_dir, image_name)

    def get_bank_id(self):
        if not self.cleaned_data:
            return None

        return self.cleaned_data["bank_name"]

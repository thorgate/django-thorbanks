import logging

from django.http import HttpResponse, HttpResponseRedirect, QueryDict
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from thorbanks import settings
from thorbanks.forms import IPizzaAuthRequest, PaymentRequest
from thorbanks.signals import (
    auth_failed,
    auth_succeeded,
    transaction_failed,
    transaction_succeeded,
)
from thorbanks.utils import verify_signature


logger = logging.getLogger(__name__)


def get_request_data(request):
    if request.method == "POST":
        return request.POST

    return request.GET


class PaymentError(Exception):
    """Generic error class."""


class AuthError(Exception):
    """Generic error class."""


@csrf_exempt
def response(request):
    data = get_request_data(request)
    if "VK_MAC" not in data:
        raise PaymentError("VK_MAC not in request")

    klass = settings.get_model("Transaction")
    transaction = get_object_or_404(klass, pk=data["VK_STAMP"])

    # Set proper encoding and get the data again (this time in correct encoding)
    request.encoding = "UTF-8"

    # We have to manually replace POST after changing encoding because of a Django bug (?)
    request.POST = QueryDict(request.body, encoding=request.encoding)
    data = get_request_data(request)

    signature_valid = verify_signature(
        data, transaction.bank_name, data["VK_MAC"], response=True
    )
    if not signature_valid:
        raise PaymentError("Invalid signature. ")

    if data["VK_SERVICE"] == "1111":
        if transaction.status == klass.STATUS_PENDING:
            # Mark purchase as complete
            transaction.status = klass.STATUS_COMPLETED
            transaction.save()
            transaction_succeeded.send(klass, transaction=transaction, request=request)
    elif data["VK_SERVICE"] == "1911":
        if transaction.status == klass.STATUS_PENDING:
            # Mark purchase as failed
            transaction.status = klass.STATUS_FAILED
            transaction.save()
            transaction_failed.send(klass, transaction=transaction, request=request)
    else:
        logging.critical(
            "thorbanks.views.response(): Got invalid VK_SERVICE code from bank: %s (transaction %s)",
            data["VK_SERVICE"],
            data["VK_STAMP"],
        )

        raise PaymentError("Bank sent confirmation with invalid VK_SERVICE!")

    if data["VK_AUTO"] == "Y":
        # This is automatic pingback from the bank - send simple 200 response as text/plain.
        return HttpResponse("request handled", content_type="text/plain")

    # This request is from the user after being redirected from the bank to our server. Redirect her further.
    if data["VK_SERVICE"] == "1111":
        url = transaction.redirect_after_success
    else:
        url = transaction.redirect_on_failure

    return HttpResponseRedirect(url)


def create_payment_request(
    bank_name,
    message,
    amount,
    currency,
    pingback_url,
    redirect_to,
    redirect_on_failure,
    extra_fields=None,
):
    return PaymentRequest(
        bank_name=bank_name,
        amount=amount,
        currency=currency,
        redirect_to=redirect_to,
        redirect_on_failure=redirect_on_failure,
        message=message,
        url=pingback_url,
        extra_fields=extra_fields,
    )


def create_auth_request(
    request, bank_name, response_url, redirect_to=None, extra_fields=None
):
    request_form_classes = {
        "ipizza": IPizzaAuthRequest,
    }
    form_cls = request_form_classes.get(settings.get_link_protocol(bank_name))
    if form_cls is None:
        return None

    return form_cls(
        bank_name=bank_name,
        response_url=response_url,
        redirect_to=redirect_to or response_url,
        extra_fields=extra_fields,
    )


class AuthResponseView(View):
    def __init__(self, **kwargs):
        self.data = None
        self.url = None
        self.auth = None

        super(AuthResponseView, self).__init__(**kwargs)

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        self.data = get_request_data(request)

        if "VK_MAC" in self.data:
            self.handle_ipizza(request)
        else:
            raise AuthError("Invalid request (unknown protocol)")

        return super(AuthResponseView, self).dispatch(request, *args, **kwargs)

    def handle_ipizza(self, request):
        klass = settings.get_model("Authentication")
        auth = get_object_or_404(klass, pk=self.data.get("VK_NONCE", None))

        # Set proper encoding and get the data again (this time in correct encoding)
        request.encoding = "UTF-8"

        # We have to manually replace POST after changing encoding because of a Django bug (?)
        request.POST = QueryDict(request.body, encoding=request.encoding)
        self.data = get_request_data(request)

        signature_valid = verify_signature(
            self.data, auth.bank_name, self.data["VK_MAC"], auth=True, response=True
        )
        if not signature_valid:
            raise AuthError("Invalid signature. ")

        self.data = self.data.dict()

        if self.data["VK_SERVICE"] == "3013":
            if auth.status == klass.STATUS_PENDING:
                # Mark auth as complete
                auth.raw_response = self.data
                auth.status = klass.STATUS_COMPLETED
                auth.save()
                auth_succeeded.send(klass, auth=auth)

        else:
            if auth.status == klass.STATUS_PENDING:
                # Mark auth as failed
                auth.raw_response = self.data
                auth.status = klass.STATUS_FAILED
                auth.save()
                auth_failed.send(klass, auth=auth)

        # This request is from the user after being redirected from the bank to our server. Redirect her further.
        if self.data["VK_SERVICE"] == "3013":
            self.url = auth.redirect_after_success
        else:
            self.url = auth.redirect_on_failure

        self.auth = auth

        self.data["name"] = self.data.get("VK_USER_NAME")
        self.data["person_code"] = self.data.get("VK_USER_ID")

    def get(self, request, *args, **kwargs):
        return HttpResponseRedirect(self.url)

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

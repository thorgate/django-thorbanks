from django.utils.decorators import method_decorator
from django.views.generic import View
import logging

from django.http import HttpResponseRedirect
from django.http import HttpResponse, QueryDict
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from thorbanks import settings
from thorbanks.forms import PaymentRequest, AuthRequest
from thorbanks.utils import verify_signature
from thorbanks.signals import transaction_succeeded, auth_succeeded, auth_failed
from thorbanks.signals import transaction_failed


logger = logging.getLogger(__name__)


def get_request_data(request):
    if request.method == 'POST':
        return request.POST
    else:
        return request.GET


class PaymentError(Exception):
    """Generic error class."""


class AuthError(Exception):
    """Generic error class."""


@csrf_exempt
def response(request):
    data = get_request_data(request)
    if 'VK_MAC' not in data:
        raise PaymentError("VK_MAC not in request")

    klass = settings.get_model('Transaction')
    transaction = get_object_or_404(klass, pk=data['VK_STAMP'])

    # Set proper encoding and get the data again (this time in correct encoding)
    request.encoding = settings.get_encoding(transaction.bank_name)

    # We have to manually replace POST after changing encoding because of a Django bug (?)
    request.POST = QueryDict(request.body, encoding=request.encoding)
    data = get_request_data(request)

    signature_valid = verify_signature(data, transaction.bank_name, data['VK_MAC'])
    if not signature_valid:
        raise PaymentError("Invalid signature. ")

    if data['VK_SERVICE'] == '1101':
        if transaction.status == klass.STATUS_PENDING:
            # Mark purchase as complete
            transaction.status = klass.STATUS_COMPLETED
            transaction.save()
            transaction_succeeded.send(klass, transaction=transaction)
    elif data['VK_SERVICE'] == '1901':
        if transaction.status == klass.STATUS_PENDING:
            # Mark purchase as failed
            transaction.status = klass.STATUS_FAILED
            transaction.save()
            transaction_failed.send(klass, transaction=transaction)
    else:
        logging.critical("thorbanks.views.response(): Got invalid VK_SERVICE code from bank: %s (transaction %s)",
                         data['VK_SERVICE'], data['VK_STAMP'])

        raise PaymentError("Bank sent confirmation with invalid VK_SERVICE!")

    if data['VK_AUTO'] == 'Y':
        # This is automatic pingback from the bank - send simple 200 response.
        return HttpResponse("request handled")
    else:
        # This request is from the user after being redirected from the bank to our server. Redirect her further.
        if data['VK_SERVICE'] == '1101':
            url = transaction.redirect_after_success
        else:
            url = transaction.redirect_on_failure

        return HttpResponseRedirect(url)


def create_payment_request(bank_name, message, amount, currency, pingback_url, redirect_to, redirect_on_failure):
    return PaymentRequest(
        bank_name=bank_name,
        amount=amount,
        currency=currency,
        redirect_to=redirect_to,
        redirect_on_failure=redirect_on_failure,
        message=message,
        url=pingback_url,
    )


def create_auth_request(request, bank_name, response_url, redirect_to=None):
    return AuthRequest(
        bank_name=bank_name,
        response_url=response_url,
        redirect_to=redirect_to or response_url,
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

        if 'VK_MAC' not in self.data:
            raise AuthError("VK_MAC not in request")

        klass = settings.get_model('Authentication')
        auth = get_object_or_404(klass, pk=self.data.get('VK_RID', None))

        # Set proper encoding and get the data again (this time in correct encoding)
        request.encoding = settings.get_encoding(auth.bank_name)

        # We have to manually replace POST after changing encoding because of a Django bug (?)
        request.POST = QueryDict(request.body, encoding=request.encoding)
        self.data = get_request_data(request)

        signature_valid = verify_signature(self.data, auth.bank_name, self.data['VK_MAC'], auth=True, response=True)
        if not signature_valid:
            raise AuthError("Invalid signature. ")

        self.data = self.data.dict()

        if self.data['VK_SERVICE'] == '3012':
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
        if self.data['VK_SERVICE'] == '3012':
            self.url = auth.redirect_after_success
        else:
            self.url = auth.redirect_on_failure

        self.auth = auth

        return super(AuthResponseView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return HttpResponseRedirect(self.url)

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

import logging

from django.http import HttpResponseRedirect
from django.http import HttpResponse, QueryDict
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from thorbanks import settings
from thorbanks.forms import PaymentRequest
from thorbanks.utils import verify_signature
from thorbanks.models import Transaction
from thorbanks.signals import transaction_succeeded
from thorbanks.signals import transaction_failed


logger = logging.getLogger(__name__)


def get_request_data(request):
    if request.method == 'POST':
        return request.POST
    else:
        return request.GET


class PaymentError(Exception):
    """Generic error class."""


@csrf_exempt
def response(request):
    data = get_request_data(request)
    if 'VK_MAC' not in data:
        raise PaymentError("VK_MAC not in request")
    transaction = get_object_or_404(Transaction, pk=data['VK_STAMP'])

    # Set proper encoding and get the data again (this time in correct encoding)
    request.encoding = settings.get_encoding(transaction.bank_name)

    # We have to manually replace POST after changing encoding because of a Django bug (?)
    request.POST = QueryDict(request.body, encoding=request.encoding)
    data = get_request_data(request)

    signature_valid = verify_signature(data, transaction.bank_name, data['VK_MAC'])
    if not signature_valid:
        raise PaymentError("Invalid signature. ")

    if data['VK_SERVICE'] == '1101':
        if transaction.status == Transaction.STATUS_PENDING:
            # Mark purchase as complete
            transaction.status = Transaction.STATUS_COMPLETED
            transaction.save()
            transaction_succeeded.send(Transaction, transaction=transaction)
    elif data['VK_SERVICE'] == '1901':
        if transaction.status == Transaction.STATUS_PENDING:
            # Mark purchase as failed
            transaction.status = Transaction.STATUS_FAILED
            transaction.save()
            transaction_failed.send(Transaction, transaction=transaction)
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

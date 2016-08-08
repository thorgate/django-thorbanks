from __future__ import unicode_literals

import sys

from django import http
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.debug import ExceptionReporter
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, FormView
from thorbanks.settings import LINKS

from thorbanks.views import create_payment_request, create_auth_request, AuthResponseView, AuthError
from thorbanks.utils import pingback_url

from shop.forms import AuthForm, OrderForm
from shop.models import Order


class FrontpageView(TemplateView):
    template_name = 'frontpage.html'


class PaymentView(CreateView):
    template_name = 'payment/index.html'
    form_class = OrderForm

    def form_valid(self, form):
        # Create new Order object, with null transaction
        self.object = form.save()

        # Get urls of the order's success/failure pages
        redirect_url = reverse('order-success', kwargs={'pk': self.object.id})
        redirect_on_failure_url = reverse('order-failed', kwargs={'pk': self.object.id})

        # Allow overwriting of send_ref value via url param (this is for unittests)
        # WARNING: Don't use this in production code
        old_val = LINKS[form.cleaned_data['bank_name']].get('SEND_REF', True)
        LINKS[form.cleaned_data['bank_name']]['SEND_REF'] = self.request.GET.get('send_ref', '1') == '1'

        # Create new payment request
        payment = create_payment_request(bank_name=form.cleaned_data['bank_name'], message="My cool payment",
                                         amount=form.cleaned_data['amount'], currency='EUR',
                                         pingback_url=pingback_url(self.request),
                                         redirect_on_failure=redirect_on_failure_url,
                                         redirect_to=redirect_url)

        # restore old SEND_REF value
        LINKS[form.cleaned_data['bank_name']]['SEND_REF'] = old_val

        # Attach the pending transaction object to the Order object
        self.object.transaction = payment.transaction
        self.object.save()

        # Finally, return the HTTP response which redirects the user to the bank
        return payment.get_redirect_response()


class PaymentSuccess(DetailView):
    model = Order
    template_name = 'payment/success.html'


class PaymentFailed(DetailView):
    model = Order
    template_name = 'payment/failed.html'


class AuthenticationView(FormView):
    template_name = 'auth/index.html'
    form_class = AuthForm

    def form_valid(self, form):
        # Get urls of the order's success/failure pages
        redirect_url = self.request.build_absolute_uri(reverse('auth-complete'))

        # Create new auth request
        bank_name = form.cleaned_data['bank_name']
        auth_form = create_auth_request(
            request=self.request,
            bank_name=bank_name,
            response_url=redirect_url,
        )

        # Finally, return the HTTP response which redirects the user to the bank
        return HttpResponse(auth_form.redirect_html())


class AuthenticationCompleteView(AuthResponseView, TemplateView):
    template_name = 'auth/success.html'

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        try:
            return super(AuthenticationCompleteView, self).dispatch(request, *args, **kwargs)

        except AuthError:
            return self.get(request, *args, **kwargs)

    def validate(self, request):
        if self.auth is None or self.data is None:
            return None

        # Check if the person code is present
        if 'person_code' not in self.data:
            return None

        return self.data

    def get(self, request, *args, **kwargs):
        data = self.validate(request)

        if data is None:
            self.template_name = 'auth/failed.html'
        else:
            self.template_name = 'auth/success.html'

        return self.render_to_response(data)


def show_server_error(request):
    """
    500 error handler to show Django default 500 template
    with nice error information and traceback.
    Useful in testing, if you can't set DEBUG=True.

    Templates: `500.html`
    Context: sys.exc_info() results
     """
    exc_type, exc_value, exc_traceback = sys.exc_info()
    error = ExceptionReporter(request, exc_type, exc_value, exc_traceback)
    return http.HttpResponseServerError(error.get_traceback_html())

from django.core.urlresolvers import reverse
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView

from shop.forms import OrderForm
from shop.models import Order

from thorbanks.views import create_payment_request
from thorbanks.utils import pingback_url


class FrontpageView(CreateView):
    template_name = 'frontpage.html'
    form_class = OrderForm

    def form_valid(self, form):
        # Create new Order object, with null transaction
        self.object = form.save()

        # Get urls of the order's success/failure pages
        redirect_url = reverse('order-success', kwargs={'pk': self.object.id})
        redirect_on_failure_url = reverse('order-failed', kwargs={'pk': self.object.id})

        # Create new payment request
        payment = create_payment_request(bank_name=form.cleaned_data['bank_name'], message="My cool payment",
                                         amount=form.cleaned_data['amount'], currency='EUR',
                                         pingback_url=pingback_url(self.request),
                                         redirect_on_failure=redirect_on_failure_url,
                                         redirect_to=redirect_url)

        # Attach the pending transaction object to the Order object
        self.object.transaction = payment.transaction
        self.object.save()

        # Finally, return the HTTP response which redirects the user to the bank
        return payment.get_redirect_response()


class PaymentSuccess(DetailView):
    model = Order
    template_name = 'success.html'


class PaymentFailed(DetailView):
    model = Order
    template_name = 'failed.html'

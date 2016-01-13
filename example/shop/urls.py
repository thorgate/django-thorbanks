from __future__ import unicode_literals

from django.conf.urls import url, include

from shop.views import (FrontpageView, PaymentView, PaymentSuccess, PaymentFailed,
                        AuthenticationView, AuthenticationCompleteView)


urlpatterns = [
    url(r'^$', FrontpageView.as_view(), name='frontpage'),

    url(r'^order/$', PaymentView.as_view(), name='payment'),
    url(r'^order/(?P<pk>\d+)/success/$', PaymentSuccess.as_view(), name='order-success'),
    url(r'^order/(?P<pk>\d+)/failed/$', PaymentFailed.as_view(), name='order-failed'),

    url(r'^auth/$', AuthenticationView.as_view(), name='auth'),
    url(r'^auth/complete/$', AuthenticationCompleteView.as_view(), name='auth-complete'),

    url(r'^banks/', include('thorbanks.urls')),
]

handler500 = 'shop.views.show_server_error'

from django.conf.urls import patterns, url
from shop.views import FrontpageView, PaymentSuccess, PaymentFailed


urlpatterns = patterns('shop.views',
    url(r'^$', FrontpageView.as_view(), name='frontpage'),
    url(r'^order/(?P<pk>\d+)/success/$', PaymentSuccess.as_view(), name='order-success'),
    url(r'^order/(?P<pk>\d+)/failed/$', PaymentFailed.as_view(), name='order-failed'),
)

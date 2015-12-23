from django.conf.urls import url


urlpatterns = [
    url(r'^thorbanks_response/$', 'thorbanks.views.response', name='thorbanks_response'),
]

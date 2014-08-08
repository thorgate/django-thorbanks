from django.conf.urls import patterns, url


urlpatterns = patterns('thorbanks.views',
    url(r'^thorbanks_response/$', 'response', name='thorbanks_response'),
)

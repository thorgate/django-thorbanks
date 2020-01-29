from django.conf.urls import url

from thorbanks.views import response


urlpatterns = [
    url(r"^thorbanks_response/$", response, name="thorbanks_response"),
]

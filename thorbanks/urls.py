import django

from thorbanks.views import response


if django.VERSION >= (4, 0):
    from django.urls import re_path

    urlpatterns = [
        re_path(r"^thorbanks_response/$", response, name="thorbanks_response"),
    ]
else:
    from django.conf.urls import url

    urlpatterns = [
        url(r"^thorbanks_response/$", response, name="thorbanks_response"),
    ]

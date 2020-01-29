from django.conf.urls import include, url
from django.contrib import admin


admin.autodiscover()


urlpatterns = [
    url(r"^", include("shop.urls")),
    url(r"^admin/", admin.site.urls),
]

handler500 = "shop.views.show_server_error"

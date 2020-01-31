from django.contrib import admin

from .models import Authentication, Transaction


admin.site.register(Authentication)
admin.site.register(Transaction)

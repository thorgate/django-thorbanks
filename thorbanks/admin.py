from __future__ import unicode_literals

from django.contrib import admin

from thorbanks import settings


if not settings.manual_models('Transaction'):
    admin.site.register(settings.get_model('Transaction'))


if not settings.manual_models('Authentication'):
    admin.site.register(settings.get_model('Authentication'))

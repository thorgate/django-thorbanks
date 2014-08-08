import django.dispatch


transaction_started = django.dispatch.Signal(providing_args=['transaction'])
transaction_succeeded = django.dispatch.Signal(providing_args=['transaction'])
transaction_failed = django.dispatch.Signal(providing_args=['transaction'])

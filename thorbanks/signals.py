import django
import django.dispatch


if django.VERSION >= (4, 0):
    transaction_started = django.dispatch.Signal()
    transaction_succeeded = django.dispatch.Signal()
    transaction_failed = django.dispatch.Signal()

    auth_started = django.dispatch.Signal()
    auth_succeeded = django.dispatch.Signal()
    auth_failed = django.dispatch.Signal()
else:
    transaction_started = django.dispatch.Signal(providing_args=["transaction"])
    transaction_succeeded = django.dispatch.Signal(providing_args=["transaction"])
    transaction_failed = django.dispatch.Signal(providing_args=["transaction"])

    auth_started = django.dispatch.Signal(providing_args=["auth"])
    auth_succeeded = django.dispatch.Signal(providing_args=["auth"])
    auth_failed = django.dispatch.Signal(providing_args=["auth"])

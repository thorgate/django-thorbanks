from __future__ import unicode_literals

from thorbanks import settings
from thorbanks.abstract_models import AbstractTransaction, AbstractAuthentication
from thorbanks.loading import is_model_registered


# list of all classes in this module
__all__ = []


if not settings.manual_models('Transaction'):
    if not is_model_registered('thorbanks', 'Transaction'):
        class Transaction(AbstractTransaction):
            pass

        __all__.append('Transaction')


if not settings.manual_models('Authentication'):
    if not is_model_registered('thorbanks', 'Authentication'):
        class Authentication(AbstractAuthentication):
            pass

        __all__.append('Authentication')

from thorbanks.abstract_models import AbstractAuthentication, AbstractTransaction


class Authentication(AbstractAuthentication):
    class Meta:
        app_label = 'thorbanks'


class Transaction(AbstractTransaction):
    class Meta:
        app_label = 'thorbanks'

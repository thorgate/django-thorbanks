from django.apps import AppConfig


class ThorbanksConfig(AppConfig):
    name = "thorbanks"
    verbose_name = "Thorbanks"

    def ready(self):
        import thorbanks.checks  # NOQA

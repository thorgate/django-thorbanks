from django.apps import AppConfig

from thorbanks.settings import configure


class ThorbanksConfig(AppConfig):
    name = "thorbanks"
    verbose_name = "Thorbanks"

    def ready(self):
        import thorbanks.checks

        # Configure thorbanks settings
        # TODO: Make system checks from these
        configure()

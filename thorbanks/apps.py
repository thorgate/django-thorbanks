from django.apps import AppConfig

from thorbanks.settings import configure


class ThorbanksConfig(AppConfig):
    name = "thorbanks"
    verbose_name = "Thorbanks"

    def ready(self):
        # Configure thorbanks settings
        configure()


from django.conf import settings
from django.core.checks import register, Error


@register
def check_model_settings(app_configs, **kwargs):
    issues = []

    manual_models = getattr(settings, "THORBANKS_MANUAL_MODELS", None)

    if manual_models is None:  # No manual models
        # If no manual models then we need to ensure that `thorbanks_models` is configured correctly
        if 'thorbanks_models' not in settings.INSTALLED_APPS:
            issues.append(
                Error(
                    "thorbanks_models must be added to settings.INSTALLED_APPS when not using THORBANKS_MANUAL_MODELS",
                    id='thorbanks.E001',
                )
            )

        migration_modules = getattr(settings, 'MIGRATION_MODULES', {})

        if migration_modules.get('thorbanks', '') != 'thorbanks_models.migrations':
            issues.append(
                Error(
                    "Thorbanks is missing from settings.MIGRATION_MODULES",
                    hint='Add it to your settings like this - `MIGRATION_MODULES = { "thorbanks": "thorbanks_models.migrations" }',
                    id='thorbanks.E002',
                )
            )

    else:
        if not isinstance(manual_models, dict):
            issues.append(
                Error(
                    "settings.THORBANKS_MANUAL_MODELS must be a dict",
                    hint="see docstring of thorbanks.settings.get_model",
                    id='thorbanks.E003',
                )
            )

    return issues

import os

from django.conf import settings
from django.core.checks import Error, register

from thorbanks.settings import configure, parse_banklinks


@register
def check_model_settings(app_configs, **kwargs):
    issues = []

    manual_models = getattr(settings, "THORBANKS_MANUAL_MODELS", None)

    if manual_models is None:  # No manual models
        # If no manual models then we need to ensure that `thorbanks_models` is configured correctly
        if "thorbanks_models" not in settings.INSTALLED_APPS:
            issues.append(
                Error(
                    "thorbanks_models must be added to settings.INSTALLED_APPS when not using THORBANKS_MANUAL_MODELS",
                    id="thorbanks.E001",
                )
            )

        migration_modules = getattr(settings, "MIGRATION_MODULES", {})

        if not migration_modules.get("thorbanks_models", ""):
            issues.append(
                Error(
                    "Thorbanks is missing from settings.MIGRATION_MODULES",
                    hint="Add it to your settings like this - `MIGRATION_MODULES = "
                    '{ "thorbanks_models": "shop.thorbanks_migrations" }.',
                    id="thorbanks.E002",
                )
            )

    else:
        if manual_models is not None and not isinstance(manual_models, dict):
            issues.append(
                Error(
                    "settings.THORBANKS_MANUAL_MODELS must be a dict",
                    hint="See docstring of thorbanks.settings.get_model.",
                    id="thorbanks.E003",
                )
            )

        if "thorbanks_models" in settings.INSTALLED_APPS:
            issues.append(
                Error(
                    "thorbanks_models should not be added to "
                    "settings.INSTALLED_APPS when using THORBANKS_MANUAL_MODELS",
                    id="thorbanks.E011",
                )
            )

    return issues


@register
def check_banklink_settings(app_configs, **kwargs):
    issues = []

    links = parse_banklinks(getattr(settings, "BANKLINKS", None))

    if links and isinstance(links, dict):
        # Verify it contains valid data
        for bank_name, data in links.items():
            if len(bank_name) > 16:
                issues.append(
                    Error(
                        "settings.BANKLINKS keys are limited to 16 characters ({})".format(
                            bank_name
                        ),
                        hint="See docstring of thorbanks.settings.parse_banklinks.",
                        id="thorbanks.E005",
                    )
                )

            if not isinstance(data, dict):
                issues.append(
                    Error(
                        "settings.BANKLINKS['{}'] must be a dict with settings for the bank".format(
                            bank_name
                        ),
                        hint="See docstring of thorbanks.settings.parse_banklinks.",
                        id="thorbanks.E006",
                    )
                )

                continue

            required_keys = [
                "REQUEST_URL",
                "PRIVATE_KEY",
                "PUBLIC_KEY",
                "CLIENT_ID",
                "BANK_ID",
                "PROTOCOL",
                "PRINTABLE_NAME",
                "IMAGE_PATH",
                "TYPE",
                "ORDER",
            ]

            if data["PROTOCOL"] == "ipizza":
                for key in required_keys:
                    if key not in data or data[key] is None:
                        issues.append(
                            Error(
                                "settings.BANKLINKS['{}']: {} is required".format(
                                    bank_name, key
                                ),
                                hint="See docstring of thorbanks.settings.parse_banklinks.",
                                id="thorbanks.E007",
                            )
                        )

                if data["PUBLIC_KEY"] is not None and not os.path.isfile(
                    data["PUBLIC_KEY"]
                ):
                    issues.append(
                        Error(
                            "settings.BANKLINKS['{}']: PUBLIC_KEY file `{}` does not exist".format(
                                bank_name, data["PUBLIC_KEY"]
                            ),
                            hint="See docstring of thorbanks.settings.parse_banklinks.",
                            id="thorbanks.E008",
                        )
                    )

                if data["PRIVATE_KEY"] is not None and not os.path.isfile(
                    data["PRIVATE_KEY"]
                ):
                    issues.append(
                        Error(
                            "settings.BANKLINKS['{}']: PRIVATE_KEY file `{}` does not exist".format(
                                bank_name, data["PRIVATE_KEY"]
                            ),
                            hint="See docstring of thorbanks.settings.parse_banklinks.",
                            id="thorbanks.E009",
                        )
                    )

            else:
                issues.append(
                    Error(
                        "settings.BANKLINKS['{}']: PROTOCOL must be ipizza".format(
                            bank_name
                        ),
                        hint="See docstring of thorbanks.settings.parse_banklinks.",
                        id="thorbanks.E010",
                    )
                )

    else:
        issues.append(
            Error(
                "settings.BANKLINKS must be a dict",
                hint="See docstring of thorbanks.settings.parse_banklinks for reference.",
                id="thorbanks.E004",
            )
        )

    configure()

    return issues

import os

from django.apps import apps
from django.conf import settings


def parse_banklinks(config=None):
    """Validates settings.BANKLINKS and add defaults to items

    for a working example see the definitions in `example/settings.py`
    """
    if config is None:
        config = getattr(settings, "BANKLINKS")

    result = {}

    if isinstance(config, dict):
        for bank_name, bank_data in config.items():
            if isinstance(bank_data, dict):
                final_data = {
                    "PROTOCOL": "ipizza",
                    "TYPE": "banklink",
                    "ORDER": 99,
                    "SEND_REF": True,
                    "PUBLIC_KEY": None,
                    "PRIVATE_KEY": None,
                }

                final_data.update(bank_data)

                if final_data["PUBLIC_KEY"] is not None and os.path.isfile(
                    final_data["PUBLIC_KEY"]
                ):
                    final_data["PUBLIC_KEY"] = os.path.abspath(final_data["PUBLIC_KEY"])

                if final_data["PRIVATE_KEY"] is not None and os.path.isfile(
                    final_data["PRIVATE_KEY"]
                ):
                    final_data["PRIVATE_KEY"] = os.path.abspath(
                        final_data["PRIVATE_KEY"]
                    )

                result[bank_name] = final_data

            else:
                result[bank_name] = bank_data

    return result


def get_model_name(model_name):
    manual = getattr(settings, "THORBANKS_MANUAL_MODELS", {})
    model_full_name = manual.get(model_name, None)

    return model_full_name


def get_model(model_name):
    """THORBANKS_MANUAL_MODELS can be used to make thorbanks work with your custom Authentication/Transaction model

    Example settings:
        # Note: Make sure that "thorbanks_models" is not in INSTALLED_APPS
        # Note 2: With manual models one does not need to add thorbanks under `MIGRATION_MODULES`

        THORBANKS_MANUAL_MODELS = {
            "Authentication": "myapp.Authentication",
            "Transaction": "myapp.Transaction",
        }

    Example myapp/models.py:
        # Note: If you only use Authentication then feel free to not add Transaction model (or vice-versa).

        class Authentication(AbstractAuthentication):
            pass

        class Transaction(AbstractTransaction):
            pass

    Finally run `makemigrations myapp` to create migrations for newly registered models.
    """
    model_full_name = get_model_name(model_name) or "thorbanks_models.%s" % model_name
    return apps.get_model(model_full_name)


# Shorthand methods
def get_private_key(the_bank):
    return get_links()[the_bank]["PRIVATE_KEY"]


def get_public_key(the_bank):
    """

    Note: To extract a public key out of a bank certificate use the following command:

        $ openssl x509 -pubkey -noout -in cert.pem  > pubkey.pem
    """
    return get_links()[the_bank]["PUBLIC_KEY"]


def get_client_id(the_bank):
    return get_links()[the_bank]["CLIENT_ID"]


def get_bank_id(the_bank):
    return get_links()[the_bank]["BANK_ID"]


def get_request_url(the_bank):
    return get_links()[the_bank]["REQUEST_URL"]


def get_link_type(the_bank):
    return get_links()[the_bank]["TYPE"]


def get_link_protocol(the_bank):
    return get_links()[the_bank]["PROTOCOL"]


def get_send_ref(the_bank):
    return get_links()[the_bank]["SEND_REF"]


def get_bank_choices():
    """Returns list of (bank_name, pretty_name, image_path, order) tuples.

    Useful in forms
    """
    links = get_links()

    return [
        (
            the_bank,
            links[the_bank].get("PRINTABLE_NAME", the_bank),
            links[the_bank].get("IMAGE_PATH", the_bank),
            links[the_bank].get("ORDER", 99),
        )
        for the_bank in links
    ]


# Updated by configure method below. Do not use directly and access this value trough get_links method
_LINKS = None


def get_links():
    global _LINKS

    if _LINKS is None:
        configure()

    return _LINKS


def configure(__only_use_during_tests=None):
    global _LINKS

    _LINKS = parse_banklinks()

    if isinstance(__only_use_during_tests, dict):
        for k, v in __only_use_during_tests.items():
            _LINKS[k].update(v)

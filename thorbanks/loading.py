from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string as base_import_string


def is_model_registered(app_label, model_name):
    """Checks whether a given model is registered."""
    try:
        apps.get_registered_model(app_label, model_name)
    except LookupError:
        return False
    else:
        return True


def validate_import_string(dotted_path):
    try:
        module_path, class_name = dotted_path.rsplit(".", 1)

    except ValueError:
        raise ImproperlyConfigured("%s doesn't look like a module path" % dotted_path)

    return module_path, class_name


def import_string(dotted_path):
    return base_import_string(dotted_path)

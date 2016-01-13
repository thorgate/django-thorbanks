from __future__ import unicode_literals

from django.core.exceptions import ImproperlyConfigured

try:
    from django.utils.module_loading import import_string as base_import_string

except ImportError:
    try:
        from django.utils.module_loading import import_by_path as base_import_string

    except ImportError:
        from django.utils.importlib import import_module as base_import_string

try:
    from django.apps import apps

    get_model = apps.get_model
    get_registered_model = apps.get_registered_model

except ImportError:
    from django.db.models import get_model as django_get_model

    def get_model(app_label, model_name=None):
        if model_name is None:
            app_label, model_name = app_label.split('.')
        model = django_get_model(app_label, model_name)
        if not model:
            raise LookupError
        return model

    def get_registered_model(app_label, model_name):
        model = django_get_model(app_label, model_name, seed_cache=False, only_installed=False)
        if not model:
            raise LookupError
        return model


def is_model_registered(app_label, model_name):
    """ Checks whether a given model is registered.
    """
    try:
        get_registered_model(app_label, model_name)
    except LookupError:
        return False
    else:
        return True


def validate_import_string(dotted_path):
    try:
        module_path, class_name = dotted_path.rsplit('.', 1)

    except ValueError:
        raise ImproperlyConfigured("%s doesn't look like a module path" % dotted_path)

    return module_path, class_name


def import_string(dotted_path):
    return base_import_string(dotted_path)

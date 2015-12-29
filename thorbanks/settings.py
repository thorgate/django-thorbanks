import os

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from .loading import get_model as _get_model


def _configure():
    links = getattr(settings, 'BANKLINKS', None)

    if not links:
        raise ImproperlyConfigured(u"BANKLINKS not found in settings")

    elif not isinstance(links, dict):
        raise ImproperlyConfigured(u"settings.BANKLINKS must be dict")

    else:
        res = {}

        # Verify it contains proper data
        for bank_name, data in links.items():
            if len(bank_name) > 16:
                raise ImproperlyConfigured(u"Bank's name must be at most 16 characters (%s)" % bank_name)

            if not isinstance(data, dict):
                raise ImproperlyConfigured(u"Each bank in settings.BANKLINKS must correspond to dict with settings of that bank")

            if 'REQUEST_URL' not in data:
                raise ImproperlyConfigured(u"REQUEST_URL not found in settings for bank %s" % bank_name)

            protocol = data.get('PROTOCOL', 'ipizza')

            if protocol == 'ipizza':
                if 'PRIVATE_KEY' not in data:
                    raise ImproperlyConfigured(u"PRIVATE_KEY not found in settings for bank %s" % bank_name)

                if 'PUBLIC_KEY' not in data:
                    raise ImproperlyConfigured(u"PUBLIC_KEY not found in settings for bank %s" % bank_name)

                if 'SND_ID' not in data:
                    raise ImproperlyConfigured(u"SND_ID not found in settings for bank %s" % bank_name)

                if not os.path.isfile(data['PRIVATE_KEY']):
                    raise ImproperlyConfigured(u"Private key file %s for bank %s does not exist." % (data['PRIVATE_KEY'], bank_name))

                if not os.path.isfile(data['PUBLIC_KEY']):
                    raise ImproperlyConfigured(u"Public key file %s for bank %s does not exist." % (data['PUBLIC_KEY'], bank_name))

                data['PUBLIC_KEY'] = os.path.abspath(data['PUBLIC_KEY'])
                data['PRIVATE_KEY'] = os.path.abspath(data['PRIVATE_KEY'])

            elif protocol == 'nordea':
                if 'MAC_KEY' not in data:
                    raise ImproperlyConfigured(u"MAC_KEY not found in settings for bank %s" % bank_name)

            res[bank_name] = data

    return res


def get_model(model_name):
    return _get_model('thorbanks.%s' % model_name)


def manual_models(model_name):
    manual = getattr(settings, 'THORBANKS_MANUAL_MODELS', False)

    if manual and isinstance(manual, (list, tuple)):
        return model_name in manual

    return False


# Shorthand methods
def get_private_key(the_bank):
    return LINKS[the_bank]['PRIVATE_KEY']


def get_public_key(the_bank):
    return LINKS[the_bank]['PUBLIC_KEY']


def get_snd_id(the_bank):
    return LINKS[the_bank]['SND_ID']


def get_request_url(the_bank):
    return LINKS[the_bank]['REQUEST_URL']


def get_link_type(the_bank):
    return LINKS[the_bank]['TYPE']


def get_link_protocol(the_bank):
    return LINKS[the_bank].get('PROTOCOL', 'ipizza')


def get_bank_choices():
    """ Returns list of (bank_name, pretty_name, image_path, order) tuples.
    Useful in forms
    """
    return [(the_bank,
             LINKS[the_bank].get('PRINTABLE_NAME', the_bank),
             LINKS[the_bank].get('IMAGE_PATH', the_bank),
             LINKS[the_bank].get('ORDER', 99)) for the_bank in LINKS.keys()]


LINKS = {}


def configure():
    global LINKS

    LINKS = _configure()


configure()

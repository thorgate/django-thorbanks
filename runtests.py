import sys

from django.conf import settings
import os

settings.configure(
    DEBUG=True,
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
        }
    },
    ROOT_URLCONF='thorbanks.urls',

    INSTALLED_APPS=(
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.admin',
        'thorbanks',
    ),

    BANKLINKS = {
        'swedbank': {
            'PRINTABLE_NAME': 'Swedbank',
            'REQUEST_URL': 'https://pangalink.net/banklink/swedbank',
            'SND_ID': 'uid513131',
            'PRIVATE_KEY': os.path.join('example', 'certs', 'swed_key.pem'),
            'PUBLIC_KEY': os.path.join('example', 'certs', 'swed_cert.pem'),
            'TYPE': 'banklink',
            'IMAGE_PATH': 'swedbank.png',
            'ORDER': 1,
        },
    },
)

from django.test.runner import DiscoverRunner

test_runner = DiscoverRunner(verbosity=1)
failures = test_runner.run_tests(['thorbanks', ])

if failures:
    sys.exit(failures)

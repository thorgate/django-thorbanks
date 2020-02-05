"""
Django settings for example project.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

BASE_DIR = os.path.dirname(__file__)


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "-zta41a7+#1v=uv30j%9dxtbfh9*#=dt6l(m9$ce8p20p_=n@s"  # NOQA

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = (
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "thorbanks",
    "thorbanks_models",
    "shop",
)

MIDDLEWARE = (
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
)

ROOT_URLCONF = "example.urls"

WSGI_APPLICATION = "example.wsgi.application"


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
    }
}

# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_URL = "/static/"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates"),],
        "APP_DIRS": True,
        "OPTIONS": {
            "debug": True,
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]

# Bank links
BANKLINKS = {
    "swedbank": {
        "PRINTABLE_NAME": "Swedbank",
        "REQUEST_URL": "http://banks.maximum.thorgate.eu/banklink/swedbank-common",
        "CLIENT_ID": "uid100052",
        "BANK_ID": "HP",
        "PRIVATE_KEY": os.path.join(BASE_DIR, "..", "certs", "swed_key.pem"),
        "PUBLIC_KEY": os.path.join(BASE_DIR, "..", "certs", "swed_pub.pem"),
        "TYPE": "banklink",
        "IMAGE_PATH": "swedbank.png",
        "ORDER": 1,
    },
    "seb": {
        "PRINTABLE_NAME": "SEB",
        "REQUEST_URL": "http://banks.maximum.thorgate.eu/banklink/seb-common",
        "CLIENT_ID": "uid100036",
        "BANK_ID": "EYP",
        "PRIVATE_KEY": os.path.join(BASE_DIR, "..", "certs", "seb_key.pem"),
        "PUBLIC_KEY": os.path.join(BASE_DIR, "..", "certs", "seb_pub.pem"),
        "DIGEST_COUNTS_BYTES": True,
        "TYPE": "banklink",
        "IMAGE_PATH": "seb.png",
        "ORDER": 2,
    },
    "danske": {
        "PRINTABLE_NAME": "Danske Bank",
        "REQUEST_URL": "http://banks.maximum.thorgate.eu/banklink/sampo-common",
        "CLIENT_ID": "uid100010",
        "BANK_ID": "SAMPOPANK",
        "PRIVATE_KEY": os.path.join(BASE_DIR, "..", "certs", "danske_key.pem"),
        "PUBLIC_KEY": os.path.join(BASE_DIR, "..", "certs", "danske_pub.pem"),
        "TYPE": "banklink",
        "IMAGE_PATH": "danske.png",
        "ORDER": 3,
    },
    "nordea": {
        "PRINTABLE_NAME": "Nordea",
        "REQUEST_URL": "http://banks.maximum.thorgate.eu/banklink/ipizza",
        "CLIENT_ID": "uid100078",
        "BANK_ID": "NORDEA",
        "PRIVATE_KEY": os.path.join(BASE_DIR, "..", "certs", "nordea_key.pem"),
        "PUBLIC_KEY": os.path.join(BASE_DIR, "..", "certs", "nordea_pub.pem"),
        "TYPE": "banklink",
        "IMAGE_PATH": "nordea.png",
        "ORDER": 4,
    },
    "lhv": {
        "PRINTABLE_NAME": "LHV",
        "REQUEST_URL": "http://banks.maximum.thorgate.eu/banklink/lhv-common",
        "CLIENT_ID": "uid100049",
        "BANK_ID": "LHV",
        "PRIVATE_KEY": os.path.join(BASE_DIR, "..", "certs", "lhv_key.pem"),
        "PUBLIC_KEY": os.path.join(BASE_DIR, "..", "certs", "lhv_pub.pem"),
        "TYPE": "banklink",
        "IMAGE_PATH": "lhv.png",
        "ORDER": 5,
    },
}

# Tell django that thorbanks migrations are in thorbanks_models app
MIGRATION_MODULES = {"thorbanks_models": "shop.thorbanks_migrations"}

THORBANKS_MANUAL_MODELS = {}

# Here you can customize where the bank logos are (used by the PaymentFormMixin). This is relative to STATIC_URL and
#  must end with slash
# BANKLINK_LOGO_PATH

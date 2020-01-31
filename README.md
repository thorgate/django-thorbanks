# django-thorbanks

[![Build Status](https://travis-ci.org/thorgate/django-thorbanks.svg?branch=master)](https://travis-ci.org/thorgate/django-thorbanks)
[![Coverage Status](https://coveralls.io/repos/github/thorgate/django-thorbanks/badge.svg?branch=master)](https://coveralls.io/github/thorgate/django-thorbanks?branch=master)
[![PyPI release](https://badge.fury.io/py/django-thorbanks.png)](https://badge.fury.io/py/django-thorbanks)


Django app for integrating Estonian banklinks into your project.

## Features

Bank            | Protocol    | Authentication      | Payment
--------------- | ----------- | ------------------- | -------
Swedbank        | iPizza      | :heavy_check_mark:  | :heavy_check_mark:
SEB             | iPizza      | :heavy_check_mark:  | :heavy_check_mark:
Danske          | iPizza      | :heavy_check_mark:  | :heavy_check_mark:
LHV             | iPizza      | :heavy_check_mark:  | :heavy_check_mark:
Krediidipank    | iPizza      | :heavy_check_mark:  | :heavy_check_mark:
Nordea          | iPizza      | :heavy_check_mark:  | :heavy_check_mark:

## Usage

### Install it:

**Pip:**

```bash
pip install django-thorbanks
```

**Pipenv:**

```bash
pipenv install django-thorbanks
```

**Poetry:**

```bash
poetry add django-thorbanks
```

### Add to installed apps

```python
INSTALLED_APPS = (
    # Add the following apps:
    "thorbanks",
    "thorbanks_models",
)
```

If you want to use custom models for banklinks/authentication continue then follow instructions from [thorbanks.settings.get_model](./thorbanks/settings.py#L48). Otherwise you can continue with the next step.

Finally, make django aware that thorbanks migrations are in your local appps folder via settings.MIGRATION_MODULES:

> Note: Replace `shop` with the name of an existing app in your project.

```python
# Tell django that thorbanks migrations are in thorbanks_models app
MIGRATION_MODULES = {"thorbanks": "shop.thorbanks_models.migrations"}
```

For instructions how to continue with integration see [shop app](example/shop/urls.py) in the example project.

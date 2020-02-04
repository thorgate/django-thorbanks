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

### 1. Install it:

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

### 2. Add to installed apps

```python
INSTALLED_APPS = (
    # Add the following apps:
    "thorbanks",
    "thorbanks_models",
)
```

### 3. Configure and create migrations:

**With MANUAL_MODELS:**

- Remove `"thorbanks_models"` from `INSTALLED_APPS`
- follow instructions from [thorbanks.settings.get_model](./thorbanks/settings.py#L59).

**With default models:**

Make django aware that thorbanks migrations are in your local apps folder via settings.MIGRATION_MODULES:

> Note: Replace `shop` with the name of an existing app in your project.

```python
# Tell django that thorbanks migrations are in thorbanks_models app
MIGRATION_MODULES = {"thorbanks": "shop.thorbanks_models.migrations"}
```

### 4. Link it to your Order model

> Note: When using MANUAL_MODELS replace `thorbanks_models` with your local app name

```python
class Order(models.Model):
    # ... other fields
    transaction = models.OneToOneField(
        "thorbanks_models.Transaction", null=True, on_delete=models.SET_NULL
    )
```

### 5. Include thorbanks urls

```python
urlpatterns = [
    # This is where the user will be redirected after returning from the banklink page
    url(r"^banks/", include("thorbanks.urls")),
]
```

### 6. Add listeners to banklinks success & failure callbacks:

See [example.shop.models.banklink_success_callback](example/shop/models.py#L23) and [example.shop.models.banklink_failed_callback](example/shop/models.py#L44).

### 7. Create views and forms for payments:

see [example.shop.views](example/shop/views.py) and [example.shop.views](example/shop/forms.py).

## iPizza protocol

- [Test service](https://banks.maximum.thorgate.eu/et/info)
- [Swedbank](https://www.swedbank.ee/business/cash/ecommerce/ecommerce?language=EST)
    - [Spec](https://www.swedbank.ee/static/pdf/business/d2d/paymentcollection/Pangalingi_paringute_tehniline_spetsifikatsioon_09_10_2014.pdf)
- [SEB](https://www.seb.ee/ariklient/igapaevapangandus/maksete-kogumine/maksete-kogumine-internetis/pangalingi-tehniline)
- [LHV Bank](https://www.lhv.ee/pangateenused/pangalink/)

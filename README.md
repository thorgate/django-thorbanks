django-thorbanks
================

[![Build Status](https://travis-ci.org/thorgate/django-thorbanks.svg?branch=master)](https://travis-ci.org/thorgate/django-thorbanks)
[![Coverage Status](https://coveralls.io/repos/github/thorgate/django-thorbanks/badge.svg?branch=master)](https://coveralls.io/github/thorgate/django-thorbanks?branch=master)
[![PyPI release](https://badge.fury.io/py/django-thorbanks.png)](https://badge.fury.io/py/django-thorbanks)


Django app for integrating Estonian banklinks into your project.



Features
--------

Bank            | Protocol    | Authentication      | Payment
--------------- | ----------- | ------------------- | -------
Swedbank        | iPizza      | :heavy_check_mark:  | :heavy_check_mark:
SEB             | iPizza      | :heavy_check_mark:  | :heavy_check_mark:
Danske          | iPizza      | :heavy_check_mark:  | :heavy_check_mark:
LHV             | iPizza      | :heavy_check_mark:  | :heavy_check_mark:
Krediidipank    | iPizza      | :heavy_check_mark:  | :heavy_check_mark:
Nordea          | iPizza      | :heavy_check_mark:  | :heavy_check_mark:
Nordea          | SOLO<sup>1</sup>    | :heavy_check_mark:  | :x:

<sup>1</sup>: Nordea SOLO protocol api is considered deprecated and will be removed in the near future (since Nordea also supports iPizza protocol)

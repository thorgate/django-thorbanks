.PHONY: flake8 test coverage


flake8:
	flake8 thorbanks example tests

coverage:
	py.test --cov-config .coveragerc --cov=thorbanks --cov-report html --cov-report term-missing

test:
	py.test -n auto

tox-test:
	py.test -n auto --liveserver 127.0.0.1:10000-10100

test-slow:
	py.test

tox-main:
	tox -e py34-django18,py34-django,py34-django17,py34-django16,19,coverage,flake8

tox-py2:
	tox -e py27-django15,py27-django16,py27-django17,py27-django18,py27-django19

tox-py2-legacy:
	tox -e py27-django14,py27-django1410

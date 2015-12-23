.PHONY: flake8 test coverage


flake8:
	flake8 thorbanks example tests

coverage:
	py.test --cov-config .coveragerc --cov=thorbanks --cov-report html --cov-report term-missing

test:
	py.test -n auto

tox-test:
	py.test --liveserver 127.0.0.1:8100-8300,10000-10300,13000-13100 --driver Firefox

test-slow:
	py.test

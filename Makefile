.PHONY: flake8 test coverage

COVERAGE ?= --cov-config .coveragerc --cov=thorbanks --cov-report html --cov-report term-missing
LIVESERVER ?= --liveserver 127.0.0.1
DRIVER ?= --driver Firefox

flake8:
	flake8 thorbanks example tests

test:
	py.test $(LIVESERVER) $(DRIVER)

test-coverage:
	py.test $(LIVESERVER) $(DRIVER) $(COVERAGE)

full:
	$(MAKE) flake8
	$(MAKE) test-coverage

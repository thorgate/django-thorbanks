.PHONY: flake8 test coverage

COVERAGE ?= --cov-config .coveragerc --cov=thorbanks --cov-report html --cov-report term-missing
LIVESERVER ?= --liveserver 127.0.0.1:10000-11000
DRIVER ?= --driver Firefox

# Use `XDIST='-n auto' make <goal>` to run tests in parallel (this also works for tox, e.g. `XDIST='-n auto' tox`)
#
# Warning: The `auto` value translates to the number of available CPU cores. Use a fixed value if you get random failures related
#          to selenium and/or liveserver port allocation. Start from `cores - 1` and keep reducing the value until the failures disappear.
XDIST ?=

flake8:
	flake8 thorbanks example tests

test:
	py.test $(XDIST) $(LIVESERVER) $(DRIVER)

test-coverage:
	py.test $(XDIST) $(LIVESERVER) $(DRIVER) $(COVERAGE)

full:
	$(MAKE) flake8
	$(MAKE) test-coverage

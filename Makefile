.PHONY: quality test coverage

COVERAGE ?= --cov-config .coveragerc --cov=thorbanks --cov-report html --cov-report term-missing
LIVESERVER ?= --liveserver 127.0.0.1
DRIVER ?= --driver Firefox


black:
	black $(cmd) thorbanks example tests


isort-run:
	isort --recursive $(cmd) -p .


isort:
	$(MAKE) isort-run cmd='--diff --check-only'


isort-fix:
	$(MAKE) isort-run


quality:
	$(MAKE) black cmd='--check'
	$(MAKE) isort


test:
	py.test $(LIVESERVER) $(DRIVER)


test-coverage:
	py.test $(LIVESERVER) $(DRIVER) $(COVERAGE)


full:
	$(MAKE) quality
	$(MAKE) test-coverage

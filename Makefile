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


prospector:
	prospector .


quality:
	$(MAKE) black cmd='--check'
	$(MAKE) isort
	$(MAKE) prospector


test:
	py.test $(LIVESERVER) $(DRIVER) $(cmd)


test-coverage:
	py.test $(LIVESERVER) $(DRIVER) $(COVERAGE) $(cmd)


full:
	$(MAKE) quality
	$(MAKE) test-coverage

VENV = ./venv
PYTHON = $(VENV)/bin/python3

.PHONY: test test-all uploadtestupload  register clean bootstrap

test: bootstrap
	$(VENV)/bin/py.test tests

sdist:
	$(PYTHON) setup.py sdist

upload:
	$(PYTHON) -m twine upload dist/*

testupload:
	$(PYTHON) -m twine upload --repository testpypi dist/* --verbose

#PGCONFIGUREFLAGS="--without-icu" CFLAGS="-O2 -Wno-unguarded-availability-new" PGVERSION=17.2 ./venv/bin/python3 -m pip install --extra-index-url https://pypi.org/simple -i https://test.pypi.org/simple pgvenv==0.2.0

clean:
	rm -f MANIFEST
	rm -rf dist _deps build

all: clean sdist testupload

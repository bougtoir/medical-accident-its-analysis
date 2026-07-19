PYTHON ?= python3
VENV ?= .venv
VENV_PYTHON := $(VENV)/bin/python

.PHONY: all setup reproduce reproduce-analysis verify-sources verify-online clean-generated

all: setup reproduce

setup:
	$(PYTHON) -m venv $(VENV)
	$(VENV_PYTHON) -m pip install -r requirements.txt

reproduce:
	$(VENV_PYTHON) scripts/reproduce.py

reproduce-analysis:
	$(VENV_PYTHON) scripts/reproduce.py --skip-documents

verify-sources:
	$(VENV_PYTHON) scripts/verify_source_data.py

verify-online:
	$(VENV_PYTHON) -m pip install -r requirements-refresh.txt
	$(VENV_PYTHON) scripts/fetch_source_data.py

clean-generated:
	rm -rf reproduction/logs

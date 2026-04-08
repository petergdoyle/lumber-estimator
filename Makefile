VENV = .venv
PYTHON = $(VENV)/bin/python3
PIP = $(VENV)/bin/pip

.PHONY: setup run clean test

setup:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	touch data/.gitkeep output/.gitkeep

run:
	$(PYTHON) src/main.py

test:
	$(PYTHON) -m pytest

clean:
	rm -rf $(VENV)
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .pytest_cache

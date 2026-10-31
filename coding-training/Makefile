.PHONY: test lint check clean

PYTHON ?= python3

test:
	PYTHONPATH="packages:services:." $(PYTHON) -m unittest discover -s tests -v

lint:
	ruff check .

check: lint test

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +

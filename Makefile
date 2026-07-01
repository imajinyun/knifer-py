.PHONY: install test lint typecheck check

install:
	.venv/bin/poetry install

test:
	.venv/bin/python -m pytest

lint:
	.venv/bin/python -m ruff check src tests

typecheck:
	.venv/bin/python -m mypy src tests

check: lint typecheck test

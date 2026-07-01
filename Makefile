.PHONY: install test test-cov lint format typecheck build check clean

install:
	.venv/bin/poetry install

test:
	.venv/bin/python -m pytest

test-cov:
	.venv/bin/python -m pytest --cov=kniferpy --cov-report=term-missing

lint:
	.venv/bin/python -m ruff check src tests

format:
	.venv/bin/python -m ruff format src tests

typecheck:
	.venv/bin/python -m mypy src tests

build:
	.venv/bin/poetry build

check: lint typecheck test

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache .mypy_cache .coverage htmlcov dist build


.DEFAULT_GOAL := help

.PHONY: help install test coverage lint format check smoke

help:
	@echo "GCP Media Data Platform"
	@echo ""
	@echo "make install  - Install dependencies"
	@echo "make test     - Run unit tests"
	@echo "make coverage - Run tests with coverage"
	@echo "make lint     - Check code quality"
	@echo "make format   - Format source code"
	@echo "make check    - Run quality checks and tests"
	@echo "make smoke    - Verify GCP authentication"

install:
	python -m pip install -e '.[dev]'

test:
	python -m pytest -v

coverage:
	python -m pytest --cov=media_platform --cov-report=term-missing

lint:
	ruff check .

format:
	ruff format .

check:
	ruff check .
	ruff format --check .
	python -m pytest

smoke:
	python scripts/check_gcp.py

.PHONY: help lint format type-check test check clean dev

help:
	@echo "Available targets:"
	@echo "  make lint          - Run linting checks (ruff)"
	@echo "  make format        - Format code (ruff)"
	@echo "  make type-check    - Run type checking (mypy)"
	@echo "  make test          - Run tests (pytest)"
	@echo "  make check         - Run all checks (lint + type-check)"
	@echo "  make clean         - Clean test artifacts"
	@echo "  make dev           - Install dev dependencies"
	@echo "  make scrape        - Run the scraper"
	@echo "  make pre-commit    - Run pre-commit hooks"

lint:
	uv run ruff check bbical tests

format:
	uv run ruff format bbical tests

type-check:
	uv run mypy bbical

test:
	uv run pytest tests -v

check: lint type-check
	@echo "All checks passed!"

clean:
	rm -rf .pytest_cache __pycache__ .mypy_cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

dev:
	uv sync

scrape:
	uv run bbical

pre-commit:
	uv run pre-commit run --all-files

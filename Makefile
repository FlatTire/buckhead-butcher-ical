.PHONY: help lint format type-check test check clean dev scrape pre-commit \
         tf-init tf-fmt tf-validate tf-plan tf-apply tf-destroy tf-outputs tf-check \
         lambda-package

help:
	@echo "Available targets:"
	@echo ""
	@echo "Python/Code:"
	@echo "  make lint          - Run linting checks (ruff)"
	@echo "  make format        - Format code (ruff)"
	@echo "  make type-check    - Run type checking (mypy)"
	@echo "  make test          - Run tests (pytest)"
	@echo "  make check         - Run all checks (lint + type-check)"
	@echo "  make clean         - Clean test artifacts"
	@echo "  make dev           - Install dev dependencies"
	@echo "  make scrape        - Run the scraper"
	@echo "  make pre-commit    - Run pre-commit hooks"
	@echo ""
	@echo "Terraform/Infrastructure:"
	@echo "  make tf-init       - Initialize Terraform"
	@echo "  make tf-fmt        - Format Terraform files"
	@echo "  make tf-validate   - Validate Terraform configuration"
	@echo "  make tf-plan       - Plan Terraform changes"
	@echo "  make tf-outputs    - Show Terraform outputs"
	@echo "  make tf-check      - Format + validate (no changes)"
	@echo "  make tf-apply      - Apply Terraform changes (requires confirmation)"
	@echo "  make tf-destroy    - Destroy Terraform infrastructure"

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

# Terraform targets
tf-init:
	cd infra && terraform init

tf-fmt:
	cd infra && terraform fmt -recursive

tf-validate:
	cd infra && terraform validate

tf-check: tf-fmt tf-validate
	@echo "Terraform format and validation passed!"

tf-plan:
	cd infra && terraform plan -out=tfplan

tf-outputs:
	cd infra && terraform output

tf-apply:
	cd infra && terraform apply tfplan

tf-destroy:
	cd infra && terraform destroy

# Lambda packaging target
lambda-package:
	cd infra && \
	mkdir -p lambda_package && \
	cp lambda_handler.py lambda_package/ && \
	cp -r ../bbical lambda_package/ && \
	pip install -r ../pyproject.toml -t lambda_package/ --quiet 2>/dev/null || true && \
	cd lambda_package && zip -r ../lambda_function.zip . -q && cd .. && \
	rm -rf lambda_package && \
	echo "Lambda package created: infra/lambda_function.zip"

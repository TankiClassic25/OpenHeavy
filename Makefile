.PHONY: install run test lint format clean help

# Default target
help:
	@echo "Heavy AI Development Commands:"
	@echo "  install     Install dependencies"
	@echo "  run         Run the application"
	@echo "  test        Run tests"
	@echo "  lint        Run linting checks"
	@echo "  format      Format code"
	@echo "  clean       Clean up temporary files"

# Install dependencies
install:
	pip install --upgrade pip
	pip install -r requirements.txt

# Install development dependencies
install-dev: install
	pip install -r requirements-dev.txt

# Run the application
run:
	python src/main.py

# Run tests
test:
	pytest tests/ -v

# Run tests with coverage
test-cov:
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term

# Run linting
lint:
	flake8 src/ tests/ --max-line-length=100 --extend-ignore=E203,W503
	mypy src/ --ignore-missing-imports

# Format code
format:
	black src/ tests/ --line-length=100
	isort src/ tests/ --profile black

# Check formatting without making changes
format-check:
	black src/ tests/ --line-length=100 --check
	isort src/ tests/ --profile black --check-only

# Clean up temporary files
clean:
	find . -type d -name __pycache__ -delete
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete
	find . -name "*.pyd" -delete
	find . -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +

# Development setup
dev-setup: install-dev
	pre-commit install

# Run all checks (lint + test)
check: lint test

# Quick development cycle
dev: format lint test
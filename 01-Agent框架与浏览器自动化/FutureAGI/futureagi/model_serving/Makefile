# Makefile for UV-based Model Serving Development

.PHONY: help install install-dev sync update clean test test-cov lint format type-check serve serve-prod build docker-build docker-run health info models

# Default target
help:
	@echo "🚀 UV-based Model Serving Development Commands"
	@echo "==============================================="
	@echo ""
	@echo "Setup Commands:"
	@echo "  make install       - Install production dependencies"
	@echo "  make install-dev   - Install development dependencies"
	@echo "  make sync          - Sync dependencies from lock file"
	@echo "  make update        - Update dependencies"
	@echo "  make clean         - Clean cache and temporary files"
	@echo ""
	@echo "Development Commands:"
	@echo "  make serve         - Start development server (auto-reload)"
	@echo "  make serve-prod    - Start production server"
	@echo "  make test          - Run tests"
	@echo "  make test-cov      - Run tests with coverage"
	@echo "  make lint          - Run linting"
	@echo "  make format        - Format code"
	@echo "  make type-check    - Run type checking"
	@echo ""
	@echo "CLI Commands:"
	@echo "  make health        - Check server health"
	@echo "  make info          - Show system information"
	@echo "  make models        - List available models"
	@echo ""
	@echo "Docker Commands:"
	@echo "  make docker-build  - Build Docker image"
	@echo "  make docker-run    - Run Docker container"
	@echo ""
	@echo "Utility Commands:"
	@echo "  make requirements  - Generate requirements.txt from UV"

# Setup commands
install:
	@echo "📦 Installing production dependencies with UV..."
	uv sync --no-dev

install-dev:
	@echo "🛠️ Installing development dependencies with UV..."
	uv sync --extra dev

sync:
	@echo "🔄 Syncing dependencies from lock file..."
	uv sync --frozen

update:
	@echo "⬆️ Updating dependencies..."
	uv lock --upgrade
	uv sync

clean:
	@echo "🧹 Cleaning cache and temporary files..."
	rm -rf .uv-cache/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf dist/
	rm -rf build/
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

# Development commands
serve:
	@echo "🚀 Starting development server..."
	uv run model-serving serve --reload --log-level debug

serve-prod:
	@echo "🏭 Starting production server..."
	uv run model-serving serve --workers 4 --log-level info

test:
	@echo "🧪 Running tests..."
	uv run pytest

test-cov:
	@echo "📊 Running tests with coverage..."
	uv run pytest --cov=app --cov-report=term-missing --cov-report=html

lint:
	@echo "🔍 Running linting..."
	uv run flake8 app tests
	uv run black --check app tests
	uv run isort --check-only app tests

format:
	@echo "✨ Formatting code..."
	uv run black app tests
	uv run isort app tests

type-check:
	@echo "🔎 Running type checking..."
	uv run mypy app

# CLI commands
health:
	@echo "🏥 Checking server health..."
	uv run model-serving health

info:
	@echo "ℹ️ Showing system information..."
	uv run model-serving info

models:
	@echo "📋 Listing available models..."
	uv run model-serving models

# Docker commands
docker-build:
	@echo "🐳 Building Docker image..."
	docker build -t model-serving:latest .

docker-run:
	@echo "🏃 Running Docker container..."
	docker run -p 8080:8080 --name model-serving-container model-serving:latest

docker-stop:
	@echo "🛑 Stopping Docker container..."
	docker stop model-serving-container || true
	docker rm model-serving-container || true

# Development workflow shortcuts
dev: install-dev
	@echo "🎯 Development environment ready!"
	@echo "Run 'make serve' to start the development server"

ci: lint type-check test
	@echo "✅ CI pipeline completed successfully"

pre-commit: format lint type-check test
	@echo "🚀 Pre-commit checks completed successfully"

# Utility commands
requirements:
	@echo "📄 Generating requirements.txt from UV..."
	uv export --no-dev --format requirements-txt > requirements.txt

requirements-dev:
	@echo "📄 Generating requirements-dev.txt from UV..."
	uv export --format requirements-txt > requirements-dev.txt

# Check UV installation
check-uv:
	@command -v uv >/dev/null 2>&1 || { \
		echo "❌ UV is not installed. Please install it first:"; \
		echo "pip install uv"; \
		exit 1; \
	}
	@echo "✅ UV is installed: $$(uv --version)"

# Initialize new project (for reference)
init:
	@echo "🏗️ Initializing UV project..."
	uv init --name model-serving --package
	uv add fastapi uvicorn gunicorn

# Performance testing
bench:
	@echo "⚡ Running performance benchmarks..."
	uv run pytest -m performance

# Security audit
audit:
	@echo "🔒 Running security audit..."
	uv run pip-audit

# Create a new virtual environment
venv:
	@echo "🐍 Creating virtual environment..."
	uv venv

# Lock dependencies
lock:
	@echo "🔒 Locking dependencies..."
	uv lock

# Show dependency tree
deps:
	@echo "🌳 Showing dependency tree..."
	uv tree

# Package the application
package:
	@echo "📦 Packaging application..."
	uv build

# Install package in editable mode
install-editable:
	@echo "🔧 Installing package in editable mode..."
	uv pip install -e .

.PHONY: help install lint lint-strict check format fmt test tests clean setup-pre-commit backend-dev frontend-dev dev-backend dev-frontend be fe run

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install all dependencies
	@echo "Installing backend dependencies..."
	cd backend && poetry install
	@echo "Installing frontend dependencies..."
	cd frontend && npm install

lint: ## Run linting for both backend and frontend
	@echo "Running backend linting..."
	cd backend && poetry run black --check .
	cd backend && poetry run isort --check-only .
	cd backend && poetry run flake8 .
	@echo "Running frontend linting..."
	cd frontend && npm run lint:check
	cd frontend && npm run format:check

lint-strict: ## Run strict linting including mypy
	@echo "Running backend linting..."
	cd backend && poetry run black --check .
	cd backend && poetry run isort --check-only .
	cd backend && poetry run flake8 .
	cd backend && poetry run mypy src/
	@echo "Running frontend linting..."
	cd frontend && npm run lint:check
	cd frontend && npm run format:check

check: lint ## Alias for lint

format: ## Format code for both backend and frontend
	@echo "Formatting backend code..."
	cd backend && poetry run black .
	cd backend && poetry run isort .
	@echo "Formatting frontend code..."
	cd frontend && npm run format

fmt: format ## Alias for format

test: ## Run tests for both backend and frontend
	@echo "Running backend tests..."
	cd backend && poetry run pytest -v
	@echo "Running frontend tests..."
	cd frontend && npm run test || echo "No frontend tests configured"

tests: test ## Alias for test

clean: ## Clean up build artifacts and cache
	@echo "Cleaning backend..."
	cd backend && find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	cd backend && find . -name "*.pyc" -delete 2>/dev/null || true
	@echo "Cleaning frontend..."
	cd frontend && rm -rf node_modules/.cache 2>/dev/null || true

setup-pre-commit: ## Set up pre-commit hooks
	pip install pre-commit
	pre-commit install

backend-dev: ## Start backend development server
	cd backend && poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

frontend-dev: ## Start frontend development server
	cd frontend && npm run dev

dev-backend: backend-dev ## Alias for backend-dev
dev-frontend: frontend-dev ## Alias for frontend-dev
be: backend-dev ## Short alias for backend-dev
fe: frontend-dev ## Short alias for frontend-dev

run: ## Start both backend and frontend development servers
	@echo "Starting CampusFlow development servers..."
	@echo "Backend will be available at http://localhost:8000"
	@echo "Frontend will be available at http://localhost:3000"
	@echo "Press Ctrl+C to stop both servers"
	@trap 'kill %1 %2' INT; \
	cd backend && poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload & \
	cd frontend && npm run dev & \
	wait

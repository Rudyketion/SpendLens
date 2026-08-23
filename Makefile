# SpendLens — common dev commands.
# Usage: `make <target>`. Run `make help` to see what's available.

.PHONY: help install backend-install frontend-install \
        dev backend frontend \
        seed reset \
        test lint typecheck \
        docker docker-down clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?##' $(MAKEFILE_LIST) | awk -F':.*?##' '{printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: backend-install frontend-install ## Install both backend + frontend deps

backend-install: ## Install Python deps into a venv
	cd backend && python -m venv .venv && \
	  ./.venv/bin/pip install -U pip && \
	  ./.venv/bin/pip install -r requirements.txt pytest ruff

frontend-install: ## Install npm deps
	cd frontend && npm install --no-audit --no-fund

backend: ## Run backend with hot reload
	cd backend && ./.venv/bin/uvicorn app.main:app --reload --port 8000

frontend: ## Run frontend dev server
	cd frontend && npm run dev

dev: ## Tip: run `make backend` and `make frontend` in two terminals
	@echo "Open two terminals and run:"
	@echo "  make backend"
	@echo "  make frontend"

seed: ## Populate the DB with 3 months of demo transactions
	cd backend && ./.venv/bin/python -m app.seed

reset: ## Wipe the local SQLite DB
	rm -f backend/spendlens.db backend/data/spendlens.db
	@echo "DB reset."

test: ## Run backend tests
	cd backend && ./.venv/bin/pytest

lint: ## Lint Python code
	cd backend && ./.venv/bin/ruff check app tests

typecheck: ## Type-check the frontend
	cd frontend && npm run typecheck

docker: ## Bring everything up via docker compose
	docker compose up --build

docker-down: ## Stop and remove containers
	docker compose down

clean: ## Remove caches and build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf backend/.pytest_cache backend/.ruff_cache
	rm -rf frontend/.next frontend/node_modules/.cache

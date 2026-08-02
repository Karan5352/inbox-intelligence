.DEFAULT_GOAL := help
PY := backend/.venv/bin/python
PIP := backend/.venv/bin/pip

.PHONY: help venv install seed run api web dev test lint format bench migrate clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

venv: ## Create the backend virtualenv (Python 3.13)
	python3.13 -m venv backend/.venv
	$(PIP) install --upgrade pip

install: venv ## Install backend + frontend dependencies (fast; uses the fallback embedder)
	$(PIP) install -e "backend[dev]"
	cd frontend && npm install

install-ml: ## Add the local MiniLM embedding model (pulls PyTorch, ~1.5GB). Recommended for real inboxes.
	$(PIP) install -e "backend[ml]"

seed: ## Build the synthetic demo database
	$(PY) -m backend.scripts.seed_demo

api: ## Run the FastAPI backend (http://localhost:8000)
	backend/.venv/bin/uvicorn app.main:app --app-dir backend --reload --port 8000

web: ## Run the Next.js frontend (http://localhost:3000)
	cd frontend && npm run dev

test: ## Run backend tests
	cd backend && .venv/bin/pytest -q

lint: ## Lint + type-check the backend
	cd backend && .venv/bin/ruff check . && .venv/bin/mypy app

format: ## Auto-format the backend
	cd backend && .venv/bin/ruff format . && .venv/bin/ruff check --fix .

bench: ## Run the categorization benchmark -> docs/RESULTS.md
	$(PY) -m backend.scripts.benchmark

COUNT ?= 40
eval: ## Hand-label real emails to estimate accuracy (use COUNT=100 for a bigger sample)
	cd backend && .venv/bin/python -m scripts.evaluate_real --count $(COUNT)

eval-score: ## Re-score what you've already labelled (e.g. after corrections + re-sort)
	cd backend && .venv/bin/python -m scripts.evaluate_real --score

ab-before: ## Lock in a clean before/after baseline (CLEARS your existing corrections)
	cd backend && .venv/bin/python -m scripts.ab_test baseline --reset

ab-after: ## Score the "after" (run once you've corrected some emails + re-sorted)
	cd backend && .venv/bin/python -m scripts.ab_test after

migrate: ## Apply database migrations
	cd backend && .venv/bin/alembic upgrade head

clean: ## Remove caches and local databases
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -f backend/data/*.db

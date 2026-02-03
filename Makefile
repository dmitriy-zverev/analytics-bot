.PHONY: help install lint format typecheck test pre-commit-install migrate upgrade downgrade load-data run-bot \
        docker-build docker-up docker-down docker-logs

help:
	@echo "Available targets:"
	@echo "  install        Install dependencies using uv"
	@echo "  lint           Run ruff lint"
	@echo "  format         Run ruff format"
	@echo "  typecheck      Run mypy"
	@echo "  test           Run pytest"
	@echo "  migrate        Generate a new Alembic migration (manual message)"
	@echo "  upgrade        Apply Alembic migrations"
	@echo "  downgrade      Roll back one Alembic migration"
	@echo "  load-data      Load data/videos.json into Postgres"
	@echo "  run-bot        Run the Telegram bot (app/main.py)"
	@echo "  pre-commit-install Install pre-commit hooks"
	@echo "  docker-build   Build the Docker image"
	@echo "  docker-up      Start docker-compose services"
	@echo "  docker-down    Stop docker-compose services"
	@echo "  docker-logs    Tail docker-compose logs"

install:
	uv sync

install-dev:
	uv sync --all-extras

lint:
	uv run ruff check .

format:
	uv run ruff format .

typecheck:
	uv run mypy app

test:
	uv run pytest

pre-commit-install: install-dev
	uv run pre-commit install

migrate:
	@if [ -z "$(message)" ]; then \
		echo "Usage: make migrate message='your message'"; \
		exit 1; \
	fi
	uv run alembic revision -m "$(message)"

upgrade:
	uv run alembic upgrade head

downgrade:
	uv run alembic downgrade -1

load-data: upgrade
	PYTHONPATH=. uv run python scripts/load_data.py

run-bot:
	uv run python app/main.py

docker-build:
	docker build -t analytics-bot:latest .

docker-up:
	docker compose up -d

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f
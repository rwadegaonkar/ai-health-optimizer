.PHONY: up down build logs migrate test seed clean

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

logs-backend:
	docker compose logs -f backend

logs-frontend:
	docker compose logs -f frontend

migrate:
	docker compose exec backend alembic upgrade head

migrate-create:
	docker compose exec backend alembic revision --autogenerate -m "$(msg)"

seed:
	docker compose exec backend python -m app.seed

test:
	docker compose exec backend pytest -v

test-cov:
	docker compose exec backend pytest --cov=app --cov-report=html

shell-backend:
	docker compose exec backend bash

shell-db:
	docker compose exec db psql -U health_ai

clean:
	docker compose down -v
	rm -rf uploads/*

restart-backend:
	docker compose restart backend

restart-frontend:
	docker compose restart frontend

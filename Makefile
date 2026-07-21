.PHONY: dev down logs api-shell web-shell test test-api test-web lint lint-api lint-web fmt migrate hooks-install

## Bring up the full local stack (Postgres, Redis, API, web) via Docker Compose
dev:
	@test -f .env || cp .env.example .env
	docker compose up --build

## Activate the versioned git hooks (progress.md enforcement) for this clone
hooks-install:
	git config core.hooksPath .githooks
	@echo "git hooks active: .githooks (core.hooksPath)"

## Stop and remove containers (keeps volumes)
down:
	docker compose down

## Tail logs for all services
logs:
	docker compose logs -f

## Shell into the running API container
api-shell:
	docker compose exec api bash

## Shell into the running web container
web-shell:
	docker compose exec web sh

## Run backend + frontend test suites
test: test-api test-web

test-api:
	docker compose run --rm api pytest

test-web:
	docker compose run --rm web npm test -- --run

## Run backend + frontend linters
lint: lint-api lint-web

lint-api:
	docker compose run --rm api sh -c "ruff check . && black --check . && mypy src"

lint-web:
	docker compose run --rm web npm run lint

## Auto-format backend + frontend
fmt:
	docker compose run --rm api sh -c "ruff check --fix . && black ."
	docker compose run --rm web npm run format

## Apply database migrations
migrate:
	docker compose run --rm api alembic upgrade head

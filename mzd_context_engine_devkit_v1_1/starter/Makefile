.PHONY: dev down logs test

dev:
	docker compose up --build

down:
	docker compose down -v

logs:
	docker compose logs -f backend

test:
	docker compose run --rm backend pytest -q

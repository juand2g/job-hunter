.PHONY: up down fetch logs stats

up:
	docker compose up -d --build

down:
	docker compose down

fetch:
	docker compose exec api python -m app.runner

logs:
	docker compose logs -f api

stats:
	curl -s http://localhost:8000/stats | python3 -m json.tool

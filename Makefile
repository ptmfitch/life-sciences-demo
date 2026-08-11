.PHONY: db server web demo install stop

db:
	@if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then \
		docker compose up -d db; \
	else \
		echo "Docker unavailable — ensure local Postgres is running on :5432"; \
		echo "Example: brew services start postgresql@16"; \
	fi

server:
	cd server && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --timeout-graceful-shutdown 3

web:
	cd web && npm run dev

install:
	cd server && uv sync --extra dev
	cd web && npm install
	mkdir -p data/telemetry

demo: db
	@echo "Start two terminals:"
	@echo "  make server"
	@echo "  make web"
	@echo "Then open http://localhost:5173"

stop:
	-docker compose down 2>/dev/null || true
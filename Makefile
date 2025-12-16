# Simple make helpers for development
.PHONY: install install-backend install-frontend dev-start dev-stop test-stroke

install: install-backend install-frontend
	@echo "All install steps done."

install-backend:
	python3 -m pip install -r web_server/requirements.txt

install-frontend:
	cd frontend && npm ci

dev-start:
	bash scripts/start-dev.sh

# start and follow logs in foreground (useful for development)
dev-start-foreground:
	bash scripts/start-dev.sh --follow-logs

dev-stop:
	bash scripts/stop-dev.sh

test-stroke:
	bash scripts/test-stroke.sh

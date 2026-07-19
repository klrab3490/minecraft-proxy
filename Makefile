.PHONY: install lint format test compose-check check precommit

install:
	pip install -r ui/requirements.txt pre-commit
	pre-commit install

lint:
	ruff check .

format:
	black --check .

test:
	cd ui && python -m unittest test_app.py

compose-check:
	docker compose -f docker-compose.yml config -q
	docker compose -f docker-compose.portainer.yml config -q

check: lint format test compose-check

precommit:
	pre-commit run --all-files

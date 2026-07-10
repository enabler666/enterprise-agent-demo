.PHONY: test backend-test agent-test

test: backend-test agent-test

backend-test:
	cd backend && ./mvnw test

agent-test:
	cd agent && uv run pytest && uv run ruff check . && uv run mypy app tests

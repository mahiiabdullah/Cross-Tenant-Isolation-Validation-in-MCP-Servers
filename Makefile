.PHONY: lint typecheck test cov run-demo clean help

PY ?= python
SRC := framework attacks mcp_servers tests

help:
	@echo "Targets:"
	@echo "  make lint         ruff check $(SRC)"
	@echo "  make typecheck    mypy $(SRC)"
	@echo "  make test         pytest -q"
	@echo "  make cov          pytest --cov=framework --cov-report=term-missing"
	@echo "  make run-demo     run the demo manifest end-to-end"
	@echo "  make clean        remove caches + generated artifacts"

lint:
	ruff check $(SRC)

typecheck:
	mypy $(SRC) || true   # type-check is informational in Phase 8

test:
	$(PY) -m pytest tests/ -q

cov:
	$(PY) -m pytest tests/ --cov=framework --cov-report=term-missing

run-demo:
	$(PY) framework/cli.py run experiments/manifests/demo.yaml --output analysis/runs/demo

clean:
	rm -rf .pytest_cache .ruff_cache .mypy_cache analysis/runs/demo/*.jsonl analysis/runs/demo/report.*

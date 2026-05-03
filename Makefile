.PHONY: help install verify-sqlite ingest ingest-dry ainews lint type test clean backup

help:
	@echo "dair (deep-ai-research) — common targets"
	@echo "  make install         uv sync (Python deps)"
	@echo "  make verify-sqlite   sanity-check sqlite-vec ABI compat"
	@echo "  make ainews          run only the AINews adapter (smoke test)"
	@echo "  make ingest          run all enabled adapters"
	@echo "  make ingest-dry      dry-run all adapters; no files written"
	@echo "  make lint            ruff + mypy"
	@echo "  make test            pytest"
	@echo "  make backup          tar critical files to ~/backup/"

install:
	uv sync

verify-sqlite:
	bash ops/verify-sqlite.sh

ainews:
	uv run python -m ingest.run --adapter ainews --verbose

ingest:
	uv run python -m ingest.run

ingest-dry:
	uv run python -m ingest.run --dry-run --verbose

lint:
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy ingest mcp tests

test:
	uv run pytest

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache build dist *.egg-info

backup:
	mkdir -p ~/backup
	tar -czf ~/backup/dair-$$(date +%Y-%m-%d).tar.gz \
	    config/ evals/cases.yaml evals/runs/_history.jsonl reports/ \
	    CLAUDE.md PLAN.md NOTES.md README.md \
	    .claude/agents/ .claude/skills/ \
	    ingest/ mcp/ ops/ tests/ \
	    Makefile pyproject.toml .env.example .gitignore
	@echo "Backup written to ~/backup/dair-$$(date +%Y-%m-%d).tar.gz"

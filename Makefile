.PHONY: help install install-embed install-timers verify-sqlite ingest ingest-dry ainews \
        embed poll-authorities tag-engagements promote-arxiv eval lint test clean backup

help:
	@echo "dair (deep-ai-research) — common targets"
	@echo ""
	@echo "  Setup:"
	@echo "    make install            uv sync (core deps)"
	@echo "    make install-embed      uv sync --extra embed (adds PyTorch ~3GB)"
	@echo "    make install-timers     install systemd-user timers (background ingestion)"
	@echo "    make verify-sqlite      sanity-check sqlite-vec ABI compat"
	@echo ""
	@echo "  Ingestion (manual; usually run by systemd-timer):"
	@echo "    make ingest             run all enabled adapters"
	@echo "    make ingest-dry         dry-run; no files written"
	@echo "    make ainews             run only the AINews adapter (smoke)"
	@echo "    make embed              embed any unembedded chunks into sqlite-vec"
	@echo "    make poll-authorities   poll GitHub stars for authorities.yaml entries"
	@echo "    make tag-engagements    detect 'author' engagements from publication/authors"
	@echo "    make promote-arxiv      promote cross-mentioned arXiv papers (full-text)"
	@echo ""
	@echo "  Testing / quality:"
	@echo "    make eval               run evals/cases.yaml"
	@echo "    make lint               ruff + mypy"
	@echo "    make test               pytest"
	@echo ""
	@echo "  Maintenance:"
	@echo "    make backup             tar critical files to ~/backup/"

install:
	uv sync

install-embed:
	uv sync --extra embed

install-timers:
	bash ops/install-systemd-timers.sh

embed:
	uv run --extra embed python -m ingest.embed_pending -v

poll-authorities:
	uv run python -m ingest.poll_authorities -v

tag-engagements:
	uv run python -m ingest.tag_engagements -v

promote-arxiv:
	uv run python -m ingest.promote_arxiv -v

eval:
	uv run python -m evals.run_all

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
	uv run mypy ingest dair_mcp tests

test:
	uv run pytest

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache build dist *.egg-info

backup:
	mkdir -p ~/backup
	tar -czf ~/backup/dair-$$(date +%Y-%m-%d).tar.gz \
	    config/ evals/cases.yaml evals/runs/_history.jsonl reports/ \
	    CLAUDE.md PLAN.md NOTES.md README.md \
	    .claude/agents/ .claude/skills/ .mcp.json \
	    ingest/ dair_mcp/ benchmarks/ ops/ tests/ \
	    Makefile pyproject.toml uv.lock .env.example .gitignore
	@echo "Backup written to ~/backup/dair-$$(date +%Y-%m-%d).tar.gz"

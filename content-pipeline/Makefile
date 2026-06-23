# ──────────────────────────────────────────────
# VirtuAI Content Pipeline — Makefile
# ──────────────────────────────────────────────

.PHONY: help install test lint clean

help:
	@echo "VirtuAI Content Pipeline"
	@echo ""
	@echo "  install    Install Python dependencies"
	@echo "  test       Run test suite"
	@echo "  lint       Lint scripts with flake8"
	@echo "  clean      Remove generated content, caches, and schedules"

install:
	pip install -r requirements.txt

test:
	python -m pytest tests/ -v --tb=short

lint:
	flake8 scripts/ --max-line-length=120

clean:
	rm -rf data/output/
	rm -rf data/logs/
	rm -f data/schedule.db
	rm -rf __pycache__/
	rm -rf scripts/__pycache__/
	rm -rf .pytest_cache/
	rm -rf *.egg-info/
	find . -name "*.pyc" -delete

# Simple Makefile for common local tasks

.PHONY: venv install test frontend run

venv:
	python -m venv .venv

install: venv
	.venv/Scripts/activate && python -m pip install --upgrade pip && python -m pip install -r src/requirements.txt

test: install
	.venv/Scripts/activate && pytest

frontend:
	pnpm --dir src/frontend install && pnpm --dir src/frontend build

run: frontend
	./scripts/start.sh

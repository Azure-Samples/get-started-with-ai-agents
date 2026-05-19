# Simple Makefile for common local tasks

.PHONY: venv install test run

venv:
	python -m venv .venv

install: venv
	.venv/Scripts/activate && python -m pip install --upgrade pip && python -m pip install -r src/requirements.txt

test: install
	.venv/Scripts/activate && pytest

run:
	./scripts/start.sh

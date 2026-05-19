# Copilot instructions

Short guidance for GitHub Copilot and other AI coding agents working in this repository.

Purpose
- Help an AI code assistant find build/test/run commands and repository conventions quickly. Prefer links to existing docs in `docs/`.

Quick actions
- Setup: create a virtualenv and install deps:

  - `python -m venv .venv`
  - Windows (PowerShell): `.\.venv\Scripts\Activate.ps1`
  - `python -m pip install -r requirements-dev.txt`

- Run locally: `./scripts/start.sh` or `.\scripts\start.ps1`
- Use Make helpers: `make install`, `make run`, `make test`
- Run tests: `pytest`
- Run lint: `python -m ruff check src tests`

Where to look first
- `docs/` — developer and deployment guides. Start with [docs/local_development.md](docs/local_development.md) and [docs/deployment.md](docs/deployment.md).
- `src/` — application code and package layout.
- `infra/` — infrastructure templates used for Azure provisioning.
- `scripts/` — local helper scripts for setup and running the app.

Behavioral rules
- Link, don't copy: reference canonical docs instead of duplicating them.
- Bundle related edits into a single patch and provide a short commit message describing the change and affected files.
- When changing public-facing behavior (CLI flags, env vars), update `README.md` and the appropriate `docs/` page.
- Keep changes minimal and local to the task's scope; avoid wide-scope refactors without explicit user approval.

References
- Agent guide: [AGENTS.md](AGENTS.md)
- README: [README.md](README.md)

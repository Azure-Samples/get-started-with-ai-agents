# AGENTS.md

Concise instructions for AI coding agents working on this repository.

Purpose: help automated agents and human reviewers quickly find build/test/run commands, key directories, and where to read longer docs. Link, don't duplicate: this file points to canonical docs in `docs/`.

Quick Setup
- Python: create a virtualenv and install dependencies:

  - `python -m venv .venv`
  - Windows (PowerShell): `.\.venv\Scripts\Activate.ps1`
  - Unix: `source .venv/bin/activate`
  - `python -m pip install -r requirements.txt`

Useful Commands
- Run tests: `pytest` (see [tests/](tests/))
- Run lint/format checks: see [pyproject.toml](pyproject.toml) and `requirements-dev.txt`
- Local development and run instructions: see [docs/local_development.md](docs/local_development.md)
- Deployment docs: see [docs/deployment.md](docs/deployment.md)

Key directories
- `src/` — application source and package layout
- `docs/` — user and developer documentation (linking is preferred)
- `infra/` — Bicep templates and infra artifacts used for Azure provisioning
- `scripts/` — helper scripts for setup and post-deploy tasks

Agent Guidance (concise)
- Prefer linking to existing docs instead of copying content.
- When adding or changing public-facing CLI flags or environment variables, update both `README.md` and the relevant `docs/` page.
- Keep edits minimal and bundle related changes into a single patch.
- If making changes that affect CI or deployment, include a short note pointing to the changed file(s) in the commit message.

References
- Repository README: [README.md](README.md)
- Local dev doc: [docs/local_development.md](docs/local_development.md)
- Deployment doc: [docs/deployment.md](docs/deployment.md)

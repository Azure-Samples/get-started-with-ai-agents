# Changelog

This is a personal fork of [Azure-Samples/get-started-with-ai-agents](https://github.com/Azure-Samples/get-started-with-ai-agents). Only fork-specific changes are recorded here; upstream history lives in the source repository.

The format is based on [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- `CHANGELOG.md` at the repo root, following Keep a Changelog 1.1.0.

### Changed

### Fixed

## [0.1.0-fork] — 2026-05-19

### Added

- `integration-report.md` — read-only static analysis of backend/frontend wiring, API coverage, auth protection, and E2E flows.
- `scripts/integration_check.py` — stdlib-only integration scanner that produces the artifacts under `_integration/`.
- `_integration/` — captured scanner artifacts: `pytest_output.txt`, `api_routes.txt`, `auth_protection_checks.txt`, `frontend_network_calls.txt`, `types_chat_consumers.txt`.
- `AGENTS.md` — local agent-facing notes.
- `.vscode/tasks.json` — VS Code task wiring for the local dev loop.
- `pytest.ini` — pytest configuration for the fork's local test runs.
- `tests/conftest.py` — shared fixtures for the local unit tests.
- `tests/test_routes_unit.py` — FastAPI `TestClient`-based unit tests for `src/api/routes.py` (no Azure credentials required).
- Local start scripts, CI workflow, and agent documentation (earlier fork commits).
- Workspace configuration (`get-started-with-ai-agents.code-workspace`) for the project structure.

### Changed

- Documented local startup scripts and `Makefile` usage in fork docs.

[Unreleased]: https://github.com/chiefaccountant19/get-started-with-ai-agents/compare/v0.1.0-fork...HEAD
[0.1.0-fork]: https://github.com/chiefaccountant19/get-started-with-ai-agents/releases/tag/v0.1.0-fork

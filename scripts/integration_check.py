#!/usr/bin/env python3
"""Static integration scan for the AI Agents repo.

Walks ``src/api/`` and ``src/frontend/src/`` to extract:
  - FastAPI route declarations (path + method + whether ``auth_dependency`` is applied)
  - Frontend network calls (``fetch``, ``axios.*``, ``new EventSource``) with the URL and whether ``credentials: "include"`` is set within the same options block

Writes one file per artifact under ``_integration/`` and prints a summary table
on stdout. Optionally runs ``pytest`` and captures the output.

Usage from repo root::

    python scripts/integration_check.py
    python scripts/integration_check.py --no-pytest
    python scripts/integration_check.py --dry-run

Pure stdlib. No external dependencies.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
API_DIR = REPO_ROOT / "src" / "api"
FRONTEND_DIR = REPO_ROOT / "src" / "frontend" / "src"
OUT_DIR = REPO_ROOT / "_integration"

ROUTE_RE = re.compile(r'@(?:router|app)\.(get|post|put|patch|delete|options|head)\(\s*[\'"]([^\'"]+)[\'"]')
FRONTEND_FETCH_RE = re.compile(r'fetch\(\s*[\'"]([^\'"]+)[\'"]')
FRONTEND_AXIOS_RE = re.compile(r'axios(?:\.(get|post|put|patch|delete))?\(\s*[\'"]([^\'"]+)[\'"]')
FRONTEND_EVENTSOURCE_RE = re.compile(r'new\s+EventSource\(\s*[\'"]([^\'"]+)[\'"]')
CREDENTIALS_RE = re.compile(r'credentials\s*:\s*[\'"]([a-z\-]+)[\'"]')


@dataclass
class Route:
    file: str
    line: int
    method: str
    path: str
    auth_protected: bool


@dataclass
class NetworkCall:
    file: str
    line: int
    kind: str
    url: str
    credentials: str


def _relpath(p: Path) -> str:
    return str(p.relative_to(REPO_ROOT)).replace("\\", "/")


def scan_routes() -> list[Route]:
    routes: list[Route] = []
    for py_file in sorted(API_DIR.rglob("*.py")):
        text = py_file.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        for idx, line in enumerate(lines):
            m = ROUTE_RE.search(line)
            if not m:
                continue
            method, path = m.group(1).upper(), m.group(2)
            # Look at the next ~15 lines for the function signature's closing
            # paren and check whether auth_dependency appears in the signature.
            sig_window: list[str] = []
            for follow in lines[idx + 1: idx + 16]:
                sig_window.append(follow)
                if ")" in follow and follow.strip().endswith(("):", ") -> None:")) or follow.rstrip().endswith("):"):
                    break
            sig_text = "\n".join(sig_window)
            auth = "auth_dependency" in sig_text
            routes.append(Route(_relpath(py_file), idx + 1, method, path, auth))
    return routes


def scan_frontend_calls() -> list[NetworkCall]:
    calls: list[NetworkCall] = []
    patterns: list[tuple[str, re.Pattern[str], int]] = [
        ("fetch", FRONTEND_FETCH_RE, 1),
        ("axios", FRONTEND_AXIOS_RE, 2),
        ("EventSource", FRONTEND_EVENTSOURCE_RE, 1),
    ]
    for path in sorted(list(FRONTEND_DIR.rglob("*.ts")) + list(FRONTEND_DIR.rglob("*.tsx"))):
        if "node_modules" in path.parts:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        for idx, line in enumerate(lines):
            for kind, regex, url_group in patterns:
                m = regex.search(line)
                if not m:
                    continue
                url = m.group(url_group)
                # Look ahead up to 10 lines for a `credentials:` key in the
                # options block — the typical fetch options sit on the next
                # few lines.
                window = "\n".join(lines[idx: idx + 10])
                cred_match = CREDENTIALS_RE.search(window)
                creds = cred_match.group(1) if cred_match else "(none)"
                calls.append(NetworkCall(_relpath(path), idx + 1, kind, url, creds))
    return calls


def auth_coverage(routes: list[Route]) -> dict[str, list[Route]]:
    return {
        "protected": [r for r in routes if r.auth_protected],
        "unprotected": [r for r in routes if not r.auth_protected],
    }


def match_consumers(routes: list[Route], calls: list[NetworkCall]) -> dict[str, list[NetworkCall]]:
    by_path: dict[str, list[NetworkCall]] = {}
    for r in routes:
        # Match exact path or `/path/*` style consumer prefixes
        consumers = [c for c in calls if c.url == r.path or c.url.rstrip("/") == r.path.rstrip("/")]
        by_path[f"{r.method} {r.path}"] = consumers
    return by_path


def run_pytest(out_path: Path) -> int:
    cmd = [sys.executable, "-m", "pytest", "-q"]
    try:
        proc = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, timeout=120)
    except FileNotFoundError:
        out_path.write_text("pytest binary not found (sys.executable: " + sys.executable + ")\n")
        return 127
    out_path.write_text((proc.stdout or "") + (proc.stderr or ""))
    return proc.returncode


def write_artifact(name: str, content: str, dry_run: bool) -> None:
    target = OUT_DIR / name
    if dry_run:
        print(f"[dry-run] would write {target} ({len(content)} bytes)")
        return
    OUT_DIR.mkdir(exist_ok=True)
    target.write_text(content, encoding="utf-8")


def format_routes_text(routes: list[Route]) -> str:
    lines = ["# FastAPI routes (auto-generated by scripts/integration_check.py)", ""]
    for r in routes:
        guard = "AUTH" if r.auth_protected else "OPEN"
        lines.append(f"{r.file}:{r.line}:{r.method:6} {r.path:30} [{guard}]")
    return "\n".join(lines) + "\n"


def format_calls_text(calls: list[NetworkCall]) -> str:
    lines = ["# Frontend network calls (auto-generated)", ""]
    for c in calls:
        lines.append(f"{c.file}:{c.line}:{c.kind:11} {c.url:30} credentials={c.credentials}")
    return "\n".join(lines) + "\n"


def format_summary(routes: list[Route], calls: list[NetworkCall], coverage: dict[str, list[Route]], consumers: dict[str, list[NetworkCall]], pytest_rc: int | None) -> str:
    out = ["", "=== INTEGRATION CHECK SUMMARY ==="]
    out.append(f"Routes scanned:          {len(routes)}")
    out.append(f"  protected:             {len(coverage['protected'])}")
    out.append(f"  unprotected:           {len(coverage['unprotected'])}")
    out.append(f"Frontend network calls:  {len(calls)}")
    out.append("")
    out.append("Route -> consumer:")
    for key, cs in consumers.items():
        rendered = ", ".join(f"{c.file}:{c.line}" for c in cs) or "(no consumer)"
        out.append(f"  {key:30} -> {rendered}")
    out.append("")
    if pytest_rc is not None:
        out.append(f"pytest exit code: {pytest_rc}  (see _integration/pytest_output.txt)")
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Print plan; do not write _integration/*")
    parser.add_argument("--no-pytest", action="store_true", help="Skip pytest run")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON instead of the text summary")
    args = parser.parse_args()

    if not API_DIR.is_dir():
        print(f"ERROR: {API_DIR} not found — run from the get-started-with-ai-agents repo", file=sys.stderr)
        return 2
    if not FRONTEND_DIR.is_dir():
        print(f"ERROR: {FRONTEND_DIR} not found", file=sys.stderr)
        return 2

    routes = scan_routes()
    calls = scan_frontend_calls()
    coverage = auth_coverage(routes)
    consumers = match_consumers(routes, calls)

    write_artifact("api_routes.txt", format_routes_text(routes), args.dry_run)
    write_artifact("frontend_network_calls.txt", format_calls_text(calls), args.dry_run)
    write_artifact("auth_coverage.json", json.dumps({k: [asdict(r) for r in v] for k, v in coverage.items()}, indent=2), args.dry_run)
    write_artifact("route_consumers.json", json.dumps({k: [asdict(c) for c in v] for k, v in consumers.items()}, indent=2), args.dry_run)

    pytest_rc: int | None = None
    if not args.no_pytest and not args.dry_run:
        pytest_rc = run_pytest(OUT_DIR / "pytest_output.txt")

    if args.json:
        print(json.dumps({
            "routes": [asdict(r) for r in routes],
            "calls": [asdict(c) for c in calls],
            "coverage": {k: [asdict(r) for r in v] for k, v in coverage.items()},
            "consumers": {k: [asdict(c) for c in v] for k, v in consumers.items()},
            "pytest_rc": pytest_rc,
        }, indent=2))
    else:
        print(format_summary(routes, calls, coverage, consumers, pytest_rc))

    # Exit non-zero if any route is unprotected (Hassan's BLOCKER signal)
    return 1 if coverage["unprotected"] else 0


if __name__ == "__main__":
    sys.exit(main())

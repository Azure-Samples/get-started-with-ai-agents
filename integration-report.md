# Integration Check Report

**Repo:** `chiefaccountant19/get-started-with-ai-agents` (fork of Microsoft `Azure-Samples/get-started-with-ai-agents`)
**Branch:** `copilot`
**Commit:** `55504c0` (Add workspace configuration for project structure and agent-browser folder)
**Date:** 2026-05-19
**Method:** Read-only static analysis (greps + full reads of `src/api/` + `src/frontend/src/`) + pytest run.

Note: This repo does **not** use a `.planning/` GSD structure, so step 1 of the original plan (phase-summary extraction) did not apply. No `REQ-IDs` exist in the codebase or docs. Steps 2–10 ran against the real source.

---

## Wiring Summary

- **Connected (WIRED):** Backend ⇄ frontend chat flow end-to-end. 3 of 4 API routes have an active frontend consumer with `credentials: "include"`. Theme system, component import graph, and SSE streaming path all check out.
- **Orphaned:** 2 files (`src/frontend/src/types/chat.ts`, `src/frontend/src/components/agents/StarterMessages.tsx`).
- **Missing:** 1 backend auth gap (`/agent` not protected). 1 local-dev DX gap (no frontend build step in `scripts/start.sh` or `Makefile`).

## API Coverage (4 routes)

| Route | Definition | Consumer | Credentials sent | Status |
|---|---|---|---|---|
| `GET /` | `src/api/routes.py:168` | Server-side template render of `templates/index.html` (no fetch from JS) | n/a | **WIRED** |
| `GET /agent` | `src/api/routes.py:290` | `src/frontend/src/components/App.tsx:24` | `credentials: "include"` (App.tsx:29) | **WIRED** |
| `GET /chat/history` | `src/api/routes.py:250` | `src/frontend/src/components/agents/AgentPreview.tsx:123` | `credentials: "include"` (AgentPreview.tsx:128) | **WIRED** |
| `POST /chat` | `src/api/routes.py:302` | `src/frontend/src/components/agents/AgentPreview.tsx:229` | `credentials: "include"` (AgentPreview.tsx:235) | **WIRED** |

All routes consumed. No orphaned routes; no missing consumers for declared frontend dependencies.

## Auth Protection

Backend uses optional HTTP Basic auth via env-vars `WEB_APP_USERNAME` / `WEB_APP_PASSWORD`. When both set, `auth_dependency = Depends(authenticate)` is added to routes; when unset, `auth_dependency = None` and routes are open (`src/api/routes.py:57–77`).

| Route | `auth_dependency` applied? | File:Line |
|---|---|---|
| `GET /` | YES | `routes.py:169` |
| `GET /chat/history` | YES | `routes.py:255` |
| `POST /chat` | YES | `routes.py:308` |
| `GET /agent` | **NO** | `routes.py:290–292` (signature lacks `_ = auth_dependency`) |

## E2E Flows

| Flow | Trace | Status |
|---|---|---|
| **Page load** | Browser → `GET /` → Jinja renders `index.html` → loads `/static/react/assets/main-react-app.js` → `main.tsx` mounts `<App />` into `#react-root` | **WIRED** (build artifact must exist — see WARNING 1) |
| **Agent metadata** | `App.tsx:22-78` mounts → `useEffect` fetches `GET /agent` → backend reads `app.state.agent_version_details` + builds `agentPlaygroundUrl` → JSON returned → `setAgentDetails(data)` | **WIRED** |
| **Chat history load** | `AgentPreview.tsx:190` mounts → `loadChatHistory()` → `GET /chat/history` (cookies: `conversation_id`, `agent_id`) → backend creates/retrieves OpenAI Conversation → returns JSON message array → prepended to `messageList` | **WIRED** |
| **Send chat message (SSE)** | User submits via `ChatInput` → `onSend` → `POST /chat` with `{ message }` → backend creates StreamingResponse from `get_result()` → emits `data: {...}\n\n` SSE frames → frontend parses via `response.body.getReader()` + `TextDecoder` + manual `\n`-split, `data: ` strip, `JSON.parse` (AgentPreview.tsx:284–404) → renders deltas via `appendAssistantMessage` | **WIRED** |

## Detailed Findings

### BLOCKER 1 — `/agent` route bypasses HTTP Basic auth

**File:** `src/api/routes.py:290–299`

```python
@router.get("/agent")
async def get_chat_agent(
    agent: AgentVersionDetails = Depends(get_agent_version_details),
):
    wsid = os.environ.get("AZURE_EXISTING_AIPROJECT_RESOURCE_ID")
    agent_id = os.environ.get("AZURE_EXISTING_AGENT_ID")
    agent_name = agent_id.split(":")[0]
    agent_version = agent_id.split(":")[1]
    agent_playground_url = f"https://ai.azure.com/nextgen/r/{encode_project_resource_id(wsid)}/build/agents/{quote(agent_name)}/build?version={agent_version}"
    return JSONResponse(content={"name": agent.name, "metadata": agent.metadata, "agentPlaygroundUrl": agent_playground_url})
```

Compare to `/chat/history` (line 250-256), `/chat` (line 302-309), and `/` (line 168-175) — all include `_ = auth_dependency` in the signature. `/agent` does not.

**Impact:** When `WEB_APP_USERNAME` + `WEB_APP_PASSWORD` are set as an access gate, an unauthenticated client can still call `GET /agent` and exfiltrate:
- agent display name and full metadata dictionary
- `agentPlaygroundUrl` which embeds the encoded Azure AI Project resource ID + agent name + version

This leaks information about the underlying Azure AI Foundry resource even when the app is configured for restricted access. If the deployment additionally fronts the app with App Service Easy Auth (per `docs/azure_app_service_auth_setup.md`), Easy Auth would still protect it — but the in-app Basic auth dependency does not.

**Fix:** Add `_ = auth_dependency` to the `/agent` signature, matching the other three routes.

### WARNING 1 — No frontend build step in start scripts

**Files:** `scripts/start.sh`, `Makefile`, `src/frontend/vite.config.ts:13`

Vite is configured to write the React bundle to `../api/static/react/` (i.e., `src/api/static/react/`). The Jinja template `src/api/templates/index.html:8,13` references:
- `/static/react/assets/main-react-app.css`
- `/static/react/assets/main-react-app.js`

The parent `StaticFiles` mount at `src/api/main.py:120` serves `/static/*` from `src/api/static/`, so the React subpath WILL be served correctly **once the bundle exists**. However:

- `src/api/static/react/` does **not exist** in the current working tree (only `src/api/static/assets/template-images/` is present).
- Neither `scripts/start.sh` nor `Makefile` runs `pnpm install` + `pnpm build` in `src/frontend/` before starting gunicorn.
- The commented-out `app.mount("/static/react", ...)` in `main.py:124–125` is redundant given the parent `/static` mount — not strictly needed, but the comment block creates confusion.

**Impact:** Fresh-clone local dev (`make run` / `./scripts/start.sh`) starts gunicorn and serves `/` → `index.html` → 404 on the JS/CSS bundles → blank `#react-root`. User-confirmed the app is "still working" in their environment, which means the build artifacts exist on their machine — the gap is in the published bootstrap path, not the running deployment.

**Fix:** Add a `frontend` or `build` Make target (`pnpm --dir src/frontend install && pnpm --dir src/frontend build`) and prepend it to `run`, or document the manual build step prominently in `docs/local_development.md`.

### WARNING 2 — Orphaned types file

**File:** `src/frontend/src/types/chat.ts`

Defines `IMessage` and `IFileEntity`. Grep shows **zero importers** of `~/types/chat` or `../types/chat`. All chat-component consumers import from `src/frontend/src/components/agents/chatbot/types.ts` instead, which defines `IChatItem` (different shape from `IMessage`) and its own `IFileEntity` (different shape too).

**Impact:** Dead code. The two `IFileEntity` definitions have divergent shapes (`types/chat.ts` has `contentType: string`; `chatbot/types.ts` has `type: string` + `status`, `progress`, `supportFileType`, etc.) — if future code imports the wrong one, type mismatches will surface at runtime.

**Fix:** Delete `src/frontend/src/types/chat.ts` (and the `types/` directory if it ends up empty), OR consolidate the duplicate definitions into the canonical `chatbot/types.ts`.

### WARNING 3 — Orphaned component: `StarterMessages`

**File:** `src/frontend/src/components/agents/StarterMessages.tsx`

Defined as `export function StarterMessages(...)` (line 13). Grep shows **zero importers** outside its own file. The `.module.css` is referenced only inside `StarterMessages.tsx`. Not wired into `AgentPreview` or `AgentPreviewChatBot`.

**Impact:** Dead component. Vite will tree-shake the export from the bundle, but the source still ships and clutters the codebase.

**Fix:** Either wire it into the empty-chat state in `AgentPreview.tsx` (currently shows `<Title3>How can I help you today?</Title3>` at line 592 — `StarterMessages` would be a natural fit beneath it) or delete the file + its CSS module.

### WARNING 4 — Integration tests cannot run without Azure env vars

**Files:** `tests/test_evaluation.py`, `tests/test_red_teaming.py`, `tests/test_utils.py:42`

Running `pytest` with no env vars set yields:

```
FAILED tests/test_evaluation.py::test_evaluation - ValueError: Please set AZURE_EXISTING_AIPROJECT_ENDPOINT environment variable.
FAILED tests/test_red_teaming.py::test_red_teaming - ValueError: Please set AZURE_EXISTING_AIPROJECT_ENDPOINT environment variable.
2 failed in 1.22s
```

These are **integration tests** that hit live Azure AI Foundry — `test_evaluation` runs Azure AI Evaluation SDK against the deployed agent; `test_red_teaming` runs Azure AI Red Teaming against it. They're correctly designed to fail-fast when env is unset, but the repo has no pure-unit-test coverage of `src/api/routes.py`, `src/api/blob_store_manager.py`, or `src/api/search_index_manager.py`.

**Impact:** CI cannot run any meaningful tests without Azure credentials (which the GitHub Actions workflow may not have for fork PRs). Also no fast feedback loop for regressions in `routes.py` (e.g., the `/agent` auth bug above would not be caught by any existing test).

**Fix:** Add a small `tests/test_routes_unit.py` using FastAPI `TestClient` + a fake `app.state.ai_project` to cover the route shapes (status code, auth dependency, JSON shape) without hitting Azure. Tag the existing tests with `@pytest.mark.integration` and skip them by default.

### WARNING 5 — Duplicate / unused imports in `routes.py`

**File:** `src/api/routes.py:50`

```python
from fastapi import FastAPI, Depends, HTTPException, status
```

`FastAPI` is imported but never used in this file (the app instance is constructed in `main.py`). `Depends`, `HTTPException` are re-imports from line 12. Cosmetic, but the file already imports `fastapi` twice in different shapes.

**Fix:** Remove the duplicate import block at lines 50–53.

### Note — SSE stream parsing is fragile but functional

**File:** `src/frontend/src/components/agents/AgentPreview.tsx:284–404`

The frontend parses SSE manually via `response.body.getReader()` + `TextDecoder` + line-splitting on `\n`. This works against the backend's current `f"data: {json.dumps(data)}\n\n"` format because `json.dumps` never embeds raw newlines.

Theoretical fragility: if backend ever streams an SSE `data:` field whose JSON contains a literal `\n` (it cannot today because `json.dumps` escapes them), the manual parser would split mid-event and `JSON.parse` would throw. Not a current bug — but using the `EventSource` API or a library like `eventsource-parser` would be more robust for future changes.

Not flagged as WARNING because no concrete failure exists today.

## Requirements Integration Map

No `REQ-*` identifiers exist in the codebase or docs. Mapping not applicable.

## Files in `_integration/`

- `pytest_output.txt` — pytest run output (2 failures, both integration tests requiring Azure env)
- `api_routes.txt` — `grep` of all `@router.*` decorators in `src/api/`
- `auth_protection_checks.txt` — `grep` of auth-related symbols in `src/api/`
- `frontend_network_calls.txt` — `grep` of all `fetch(`, `axios.`, `EventSource(` in `src/frontend/src/`
- `types_chat_consumers.txt` — empty (confirms `types/chat.ts` is orphaned)

## Verdict

The end-to-end happy path (browser → `/` → React app → `/agent` → `/chat/history` → `POST /chat` SSE) is fully WIRED. The one BLOCKER is the `/agent` auth gap — small, mechanical fix (4 characters). The WARNINGS are dead code (2 files), local-dev bootstrap friction (no frontend build target), and a unit-test coverage gap. None of the WARNINGS are blocking.

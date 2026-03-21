# Deployment Guide

This guide covers three ways to deploy the AI Agents application, from the simplest quick-start path through to a fully Power Platform-integrated option.

## What you're deploying

A full-stack AI chat application:
- **Frontend:** React 19 + Fluent UI (TypeScript, Vite)
- **Backend:** Python FastAPI + Azure AI Projects SDK
- **AI:** Azure AI Foundry Agent Service with document knowledge retrieval
- **Infra:** Azure Container Apps, Azure OpenAI, optional Azure AI Search

---

## Comparison: which option is right for you?

| | [Option A](#option-a--azure-container-apps-recommended) | [Option B](#option-b--power-apps-code-app--python-backend) | [Option C](#option-c--power-apps-code-app--foundry-connector-preview) |
|---|---|---|---|
| **Hosting** | Azure Container Apps | Azure (backend) + Power Apps (frontend) | Power Apps (frontend) + minimal Azure |
| **Python backend required** | Yes | Yes (modified) | No — for AI chat |
| **Real-time streaming** | ✅ Yes | ✅ Yes | ❌ No (full response only) |
| **Power Platform governance** | ❌ | ✅ | ✅ |
| **Microsoft Entra auth** | Optional | Built-in | Built-in |
| **Setup effort** | Low | Medium (one-time template refactor) | Medium (one-time, simpler backend) |
| **Status** | ✅ GA | ✅ GA | ⚠️ Preview |

**Not sure which to pick?** Start with Option A. If your organisation is already on Power Platform and wants central governance across multiple app deployments, Option B is the right long-term investment. Option C is worth revisiting once the Foundry connector reaches GA.

---

## Prerequisites (all options)

- An [Azure subscription](https://azure.microsoft.com/free/) with the following permissions:
  - `Microsoft.Authorization/roleAssignments/write` at subscription scope
  - `Microsoft.Resources/deployments/write` at subscription scope
- [Azure Developer CLI (`azd`)](https://aka.ms/install-azd) version **≥ 1.14.0**
- [Azure CLI](https://docs.microsoft.com/cli/azure/install-azure-cli)
- [Git](https://git-scm.com/downloads)

**Region requirements:** Choose a region where all of the following are available — Microsoft Foundry, Azure Container Apps, Azure Container Registry, Azure AI Search, and your chosen GPT model. Good options include: East US, East US 2, Japan East, UK South, Sweden Central.

---

## Option A — Azure Container Apps (recommended)

The standard deployment path. Everything runs in Azure; `azd up` provisions all infrastructure and deploys the app in one command (~7–10 minutes).

### Quick start (GitHub Codespaces — no local tooling needed)

1. Open the project in Codespaces:
   [![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/Azure-Samples/get-started-with-ai-agents)

2. In the terminal, authenticate with Azure:
   ```shell
   az login
   azd auth login
   ```

3. Deploy:
   ```shell
   azd up
   ```
   You'll be prompted for an environment name, subscription, and region.

4. When complete, `azd` prints the app URL. Open it in your browser and try asking: _"What products does Contoso offer?"_

### Local clone

```shell
# Clone and initialise
azd init -t get-started-with-ai-agents

# Authenticate
az login
azd auth login

# Deploy
azd up
```

### Local development server (after deploying to Azure)

Use this to iterate on code without redeploying to Azure each time.

**On Linux/macOS:**
```shell
python3 -m venv .venv
source .venv/bin/activate
cd src
python -m pip install -r requirements.txt
cd frontend
pnpm run setup      # installs deps and builds the React app
cd ..
python -m uvicorn "api.main:create_app" --factory --reload
# → http://127.0.0.1:8000
```

**On Windows:**
```shell
python -m venv .venv
.venv\scripts\activate
cd src
python -m pip install -r requirements.txt
cd frontend
pnpm run setup
cd ..
python -m uvicorn "api.main:create_app" --factory --reload
```

> The app reads Azure credentials from `.azure/<environment-name>/.env`, which is created automatically by `azd up`.

### Key optional settings

```shell
# Increase model quota for better performance (recommended before azd up)
azd env set AZURE_AI_AGENT_DEPLOYMENT_CAPACITY 100

# Use Azure AI Search instead of OpenAI file search
azd env set USE_AZURE_AI_SEARCH_SERVICE true

# Enable Azure Monitor tracing
azd env set ENABLE_AZURE_MONITOR_TRACING true

# Change the AI model
azd env set AZURE_AI_AGENT_MODEL_NAME gpt-4o
azd env set AZURE_AI_AGENT_MODEL_VERSION 2024-11-20
```

### Redeploy after code changes

```shell
azd deploy
```

### Teardown

```shell
azd down
```

---

## Option B — Power Apps Code App + Python backend

**When to use:** Your organisation is already on Microsoft 365 / Power Platform and wants centralised governance (DLP, deployment pipelines, admin inventory) across multiple AI app deployments. This is a one-time template refactor — once done, every future deployment follows the same governed pattern.

### Architecture

```
[Power Apps Code App (React UI)]
         ↓ HTTPS + Entra bearer token
[Azure Container Apps / Azure Functions (FastAPI backend)]
         ↓
[Azure AI Foundry Agent Service]
```

The Python backend stays in Azure; Power Apps governs and serves the frontend.

### One-time code changes required

These changes are made once to the template and inherited by all future deployments:

1. **CORS** — Add CORS middleware to `src/api/main.py` to allow requests from the Power Apps origin:
   ```python
   from fastapi.middleware.cors import CORSMiddleware
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://*.powerapps.com"],
       allow_methods=["*"],
       allow_headers=["Authorization", "Content-Type"],
   )
   ```

2. **Authentication** — Replace HTTP Basic Auth in `src/api/routes.py` with Microsoft Entra (Azure AD) bearer token validation. The Code App provides the user's Entra token; the backend validates it using `azure-identity`.

3. **Configurable API URL** — Replace the hardcoded relative API paths in the React frontend (`/chat`, `/agent`, `/chat/history`) with a configurable base URL passed in as a Code App property or environment variable.

4. **Code App scaffold** — Adapt `src/frontend/` to the Power Apps Code Apps project structure using the [npm-based Code Apps CLI](https://learn.microsoft.com/en-us/power-apps/developer/code-apps/overview):
   ```shell
   npm install -g @microsoft/powerplatform-code-apps
   pac code init --framework react
   ```

5. **Custom Connector** — Register the Azure-hosted backend API as a Custom Connector in Power Platform admin, pointing to the Container Apps URL.

### Deployment steps

1. Deploy the backend to Azure as normal: `azd up`
2. Register the backend URL as a Custom Connector in the [Power Platform admin center](https://admin.powerplatform.microsoft.com)
3. Build and publish the Code App:
   ```shell
   pac code push --environment <your-environment-id>
   ```
4. Share the app from the Power Platform admin center

### References

- [Power Apps Code Apps overview](https://learn.microsoft.com/en-us/power-apps/developer/code-apps/overview)
- [Power Apps Code Apps architecture](https://learn.microsoft.com/en-us/power-apps/developer/code-apps/architecture)
- [Code Apps samples on GitHub](https://github.com/microsoft/PowerAppsCodeApps)

---

## Option C — Power Apps Code App + Foundry Agent Service connector ⚠️ Preview

**When to use:** You want the cleanest possible architecture with the least backend overhead. Watch this option — it significantly simplifies the stack, but the connector is currently in preview.

### Architecture

```
[Power Apps Code App (React UI)]
         ↓ Power Platform built-in connector
[Azure AI Foundry Agent Service connector (preview)]
         ↓
[Azure AI Foundry / Foundry Agent Service]
```

The [Azure AI Foundry Agent Service connector](https://learn.microsoft.com/en-us/connectors/azureagentservice/) exposes an **Invoke Agent** action that calls your Azure AI Foundry agent directly from Power Apps — no custom Python backend needed for the core AI chat path.

### What this eliminates vs. Option B

- The FastAPI application and its Azure hosting (for AI chat)
- Custom auth implementation (Entra is built-in via Power Platform)
- CORS configuration

### What still needs a solution

- **File uploads and knowledge base management** — `blob_store_manager.py` and `search_index_manager.py` have no direct equivalent in the connector. Options:
  - Use Power Automate flows to manage file uploads to Azure Blob Storage
  - Keep a slim Azure Function just for file management operations

### Current limitations

| Limitation | Impact |
|---|---|
| **No SSE streaming** | Responses arrive as a single block rather than token-by-token. The chat UX feels slower for longer responses. |
| **Preview status** | API surface may change; not recommended for production workloads yet. |
| **Connector auth** | Requires users to have an Azure AI Foundry connection configured in Power Platform. |

### Recommendation

Revisit Option C when the connector reaches GA. The architecture is the most elegant of the three — eliminating the Python backend entirely for AI workloads — and it becomes the right default for new deployments once stability is confirmed.

### References

- [Azure AI Foundry Agent Service connector](https://learn.microsoft.com/en-us/connectors/azureagentservice/)
- [Foundry Agent Service overview](https://learn.microsoft.com/en-us/azure/foundry/agents/overview)
- [Logic Apps + Foundry Agent Service](https://learn.microsoft.com/en-us/azure/logic-apps/add-agent-action-create-run-workflow)

---

## Verifying your deployment

Regardless of option, confirm the app is working by asking the agent:

> _"What products does Contoso offer?"_

The agent should respond with citations from the sample product documents in `src/files/`. If it does, knowledge retrieval is working correctly.

## Troubleshooting

See [docs/troubleshooting.md](docs/troubleshooting.md) for common issues including quota errors, permission errors, and region availability.

For quota guidance, see [docs/deploy_customization.md](docs/deploy_customization.md).

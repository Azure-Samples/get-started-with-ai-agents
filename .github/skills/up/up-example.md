# Up Skill — Example Run

This is a sanitized example of a full `/up` skill execution.

---

## Steps Overview

> **Up Skill — Steps Overview** (environment: `agent-ep-212`)
>
> 1. ✅ Choose environment name
> 2. Resolve subscription
> 3. Check RBAC permissions
> 4. Resolve region
> 5. Check agent model quota
> 6. Ask about Azure AI Search
> 7. Check embedding model quota (if AI Search enabled)
> 8. Create the azd environment and set overrides
> 9. Run `azd up`
> 10. Retrieve the app endpoint
> 11. Health-check the app
> 12. Report results

---

## Step 1 — Choose environment name

### 1a. Resolve existing environment

Scanned existing azd environments. Default: `agent-ep-211`.

### 1b. Generate a suggested new name

Highest numbered environment in the `agent-ep-*` series: `agent-ep-211`.

**Suggested:** `agent-ep-212`

### 1c. Ask the user

**User selected:** Create new environment `agent-ep-212`

### Step 1½ — Check for existing AI project

No `AZURE_EXISTING_AIPROJECT_RESOURCE_ID` set — proceeding with full path.

---

## Step 2 — Resolve subscription

Auto-detected subscription from Azure CLI:

- `11111111-2222-3333-4444-555555555555` (Speech Services - DEV)

**User selected:** Speech Services - DEV (`11111111-2222-3333-4444-555555555555`)

---

## Step 3 — Check RBAC permissions

### 3a. Direct role assignments

```
Principal: 00000000-aaaa-bbbb-cccc-dddddddddddd
Direct roles: (none)
```

No direct Owner or User Access Administrator roles found on the subscription.

### 3b. Group-based role assignments

No group memberships returned (0 groups).

⚠️ **RBAC check inconclusive** — user confirmed they have permissions via PIM/JIT and chose to continue.

---

## Step 4 — Resolve region

`AZURE_LOCATION` environment variable was not set.

**User selected:** `swedencentral`

---

## Step 5 — Check agent model quota

Queried quota usage and model list for `swedencentral`.

### 5a–5b. Default agent model

```
Default model: gpt-5-mini (GlobalStandard)
Required capacity: 80
Available capacity: 9,470
```

✅ Default agent model has sufficient quota.

### 5c–5d. Better model available

Checked higher-ranked models. `gpt-5.2` (GlobalStandard) has 21,250 available — well above the 80 required.

### 5e. Suggest the best alternative

**User selected:** `gpt-5.2` (GlobalStandard, 21,250 available)

### 5f. Resolved version

```
Model: gpt-5.2
Version: 2025-12-11
SKU: GlobalStandard
Lifecycle: GenerallyAvailable
```

---

## Step 6 — Ask about Azure AI Search

**User selected:** No — disable Azure AI Search.

---

## Step 7 — Check embedding model quota

Skipped (AI Search not enabled).

---

## Step 8 — Create the azd environment and set overrides

### 8a. Create environment

```
> azd env new agent-ep-212 --no-prompt
New environment 'agent-ep-212' created and set as default
```

### 8b. Set overrides

```
azd env set AZURE_SUBSCRIPTION_ID "11111111-2222-3333-4444-555555555555"
azd env set AZURE_LOCATION "swedencentral"
azd env set AZURE_AI_AGENT_MODEL_NAME "gpt-5.2"
azd env set AZURE_AI_AGENT_DEPLOYMENT_SKU "GlobalStandard"
azd env set AZURE_AI_AGENT_MODEL_VERSION "2025-12-11"
azd env set AZURE_AI_AGENT_MODEL_FORMAT "OpenAI"
azd env set AZURE_AI_AGENT_DEPLOYMENT_CAPACITY "80"
```

All environment variables set successfully.

---

## Step 9 — Run `azd up`

```
Provisioning Azure resources...
  (✓) Resource group: rg-agent-ep-212 (10s)
  (✓) Storage account (32s)
  (✓) Log Analytics workspace (31s)
  (✓) Application Insights (6s)
  (✓) Foundry (32s)
  (✓) Model Deployment: gpt-5.2 (3s)
  (✓) Foundry project (10s)
  (✓) Container Registry (23s)
  (✓) Container Apps Environment (57s)
  (✓) Container App (24s)

Deploying service api_and_frontend...
  (✓) Done: Deploying service api_and_frontend
  - Endpoint: https://ca-api-xxxxxxxxxx.yyyyyyyyy.swedencentral.azurecontainerapps.io/

SUCCESS: Your up workflow completed in 8 minutes 24 seconds.
```

---

## Step 10 — Retrieve the app endpoint

```
https://ca-api-xxxxxxxxxx.yyyyyyyyy.swedencentral.azurecontainerapps.io/
```

---

## Step 11 — Health-check the app

```
Attempt 1 - Timeout (cold start)
Attempt 2 - HTTP 200 - App is running!
HEALTH CHECK: PASS
```

---

## Step 12 — Results

| Field | Value |
|---|---|
| Subscription | `11111111-2222-3333-4444-555555555555` |
| Environment | `agent-ep-212` |
| Resource Group | `rg-agent-ep-212` |
| Region | `swedencentral` |
| Agent Model | `gpt-5.2` (`GlobalStandard`) |
| AI Search | Disabled |
| Embedding Model | N/A |
| App URL | `https://ca-api-xxxxxxxxxx.yyyyyyyyy.swedencentral.azurecontainerapps.io/` |
| Status | ✅ **PASS** |

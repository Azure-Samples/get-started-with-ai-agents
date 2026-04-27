# Up Skill — Example Run

This is a sanitized example of a full up skill execution.

---

## Steps Overview

> **Up Skill — Steps Overview**
>
> 1. Resolve subscription
> 2. Check RBAC permissions
> 3. Resolve region
> 4. Check chat model quota
> 5. Ask about Azure AI Search
> 6. Check embedding model quota (if AI Search enabled)
> 7. Choose environment name
> 8. Create the azd environment
> 9. Set subscription, region, and model overrides
> 10. Run `azd up`
> 11. Retrieve the app endpoint
> 12. Health-check the app
> 13. Report results

---

## Step 1 — Resolve subscription

Auto-detected subscriptions:

- **azd config default:** `aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee` (Data Science VM Team)
- **Azure CLI login:** `11111111-2222-3333-4444-555555555555` (Speech Services - DEV)

**User selected:** Speech Services - DEV (`11111111-2222-3333-4444-555555555555`)

---

## Step 2 — Check RBAC permissions

### 2a. Direct role assignments

```
Principal: 00000000-aaaa-bbbb-cccc-dddddddddddd
Direct roles: (none)
```

No direct Owner or User Access Administrator roles found on the subscription.

### 2b. Group-based role assignments

Queried user's group memberships (99 groups found).

Listed all Owner / User Access Administrator assignments on the subscription:

```
User: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx -> Owner
User: yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy -> Owner
Group: gggggggg-gggg-gggg-gggg-gggggggggggg -> Owner
Group: hhhhhhhh-hhhh-hhhh-hhhh-hhhhhhhhhhhh -> Owner
Group: iiiiiiii-iiii-iiii-iiii-iiiiiiiiiiii -> User Access Administrator
User: zzzzzzzz-zzzz-zzzz-zzzz-zzzzzzzzzzzz -> User Access Administrator
```

Cross-referenced user's groups against subscription-level Owner/UAA group assignments.

✅ **Match found** — user belongs to a group with **User Access Administrator** on the subscription.

---

## Step 3 — Resolve region

`AZURE_LOCATION` environment variable was not set.

**User selected:** `swedencentral`

---

## Step 4 — Check chat model quota

Queried quota usage and model list for `swedencentral`.

```
Default model: gpt-5-mini (GlobalStandard)
Required capacity: 80
Available capacity: 9,550
```

✅ Default chat model has sufficient quota — no alternative needed.

---

## Step 5 — Ask about Azure AI Search

**User selected:** Yes — enable Azure AI Search.

---

## Step 6 — Check embedding model quota

### 6a. Default embedding model

```
Default model: text-embedding-3-small (Standard)
Status: NOT FOUND in swedencentral
```

### 6b–6d. Alternative embedding models

| Model | SKU | Available |
|---|---|---|
| text-embedding-3-large | Standard | 1,000 |
| text-embedding-3-small | GlobalStandard | 2,500 |
| text-embedding-3-large | GlobalStandard | 9,700 |
| text-embedding-ada-002 | Standard | 771 |

**User selected:** `text-embedding-3-large` / Standard / 1,000 available

### 6e. Resolved version

```
Model: text-embedding-3-large
Version: 1
SKU: Standard
Dimensions: 1536
Lifecycle: GenerallyAvailable
```

---

## Step 7 — Choose environment name

Existing environments scanned. Highest numbered environment in the `agent-ep-*` series: `agent-ep-210`.

**Suggested:** `agent-ep-211`

**User accepted** the suggested name.

---

## Step 8 — Create the azd environment

```
> azd env new agent-ep-211 --no-prompt
New environment 'agent-ep-211' created and set as default
```

---

## Step 9 — Set subscription, region, and model overrides

```
azd env set AZURE_SUBSCRIPTION_ID "11111111-2222-3333-4444-555555555555"
azd env set AZURE_LOCATION "swedencentral"
azd env set USE_AZURE_AI_SEARCH_SERVICE "true"
azd env set AZURE_AI_EMBED_MODEL_NAME "text-embedding-3-large"
azd env set AZURE_AI_EMBED_DEPLOYMENT_NAME "text-embedding-3-large"
azd env set AZURE_AI_EMBED_DEPLOYMENT_SKU "Standard"
azd env set AZURE_AI_EMBED_MODEL_VERSION "1"
azd env set AZURE_AI_EMBED_DIMENSIONS "1536"
```

All environment variables set successfully.

---

## Step 10 — Run `azd up`

> **Note:** Initial run failed with `AADSTS700082: The refresh token has expired`.
> Re-authenticated with `azd auth login`, then retried successfully.

```
Provisioning Azure resources...
  (✓) Resource group: rg-agent-ep-211 (10s)
  (✓) Log Analytics workspace (30s)
  (✓) Storage account (30s)
  (✓) Application Insights (5s)
  (✓) Foundry (24s)
  (✓) Model Deployment: gpt-5-mini (2s)
  (✓) Model Deployment: text-embedding-3-large (4s)
  (✓) Foundry project (35s)
  (✓) Search service (10m11s)
  (✓) Container Registry (23s)
  (✓) Container Apps Environment (58s)
  (✓) Container App + role assignments (~8m)

Deploying service api_and_frontend...
  (✓) Done: Deploying service api_and_frontend
  - Endpoint: https://ca-api-xxxxxxxxxx.yyyyyyyyy.swedencentral.azurecontainerapps.io/

SUCCESS: Your up workflow completed in 20 minutes 57 seconds.
```

---

## Step 11 — Retrieve the app endpoint

```
https://ca-api-xxxxxxxxxx.yyyyyyyyy.swedencentral.azurecontainerapps.io/
```

---

## Step 12 — Health-check the app

```
Attempt 1 - HTTP 200 - App is running!
HEALTH CHECK: PASS
```

---

## Step 13 — Results

| Field | Value |
|---|---|
| Subscription | `11111111-2222-3333-4444-555555555555` |
| Environment | `agent-ep-211` |
| Resource Group | `rg-agent-ep-211` |
| Region | `swedencentral` |
| Chat Model | `gpt-5-mini` (`GlobalStandard`) |
| AI Search | Enabled |
| Embedding Model | `text-embedding-3-large` (`Standard`) |
| App URL | `https://ca-api-xxxxxxxxxx.yyyyyyyyy.swedencentral.azurecontainerapps.io/` |
| Status | ✅ **PASS** |

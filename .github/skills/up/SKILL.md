---
name: up
description: Creates an azd environment, checks prerequisites (RBAC, model quota), provisions the AI agent app infrastructure via `azd up`, and health-checks the deployed app.
---

# Up Skill

## Goal

Provision a fresh Azure environment end-to-end and verify the app starts successfully.

## Before starting

When the skill is triggered, **always re-read this SKILL.md file** from disk before
executing, in case it has been updated since the last run.

Then proceed to **Step 1 (Choose environment name)** immediately — the user must pick
an environment before anything else.

## Terminal usage

All shell commands in this skill **must** be run using the `powershell` tool with
`mode="sync"`. Use a short `initial_wait` (30 seconds) for quick commands like
`az account show`, `az ad signed-in-user show`, `az role assignment list`,
`azd env list`, `azd env new`, and `azd env set`.

**Exception — `azd up` and `azd down`:** These long-running commands **must** be run
with `mode="async"` and a short `initial_wait` (10 seconds) so the user can see
streaming progress output in real time (just like running in a terminal). After
launching, **poll frequently** using `read_powershell` with a **short delay (15–20
seconds)** — this is critical so the user sees output updates as they happen, similar
to watching the command in a terminal. Keep calling `read_powershell` in a loop
(each call in a new response turn) until the command completes or you receive a
completion notification. Do NOT use long delays like 120 seconds — that defeats the
purpose of streaming output.

Chain short related commands with `&&` or `;` into a single `powershell` call
when they have no branching logic between them.

## Steps

### 1. Choose environment name

#### 1a. Resolve existing environment

First, check whether there is already a default azd environment:

```powershell
$existingEnvs = azd env list -o json 2>$null | ConvertFrom-Json
```

Find the default environment (the entry where `IsDefault` is `true` or the `DefaultEnvironment`
field is set, depending on the azd version).

#### 1b. Generate a suggested new name

Regardless of whether a default environment exists, always prepare a suggested new name
for use as a choice.

Scan `$existingEnvs` for names matching the pattern `<prefix><number>` (e.g., `agent1`,
`test-env3`, `agent-qt-2`). If found, take the one with the **highest number** and suggest
the next increment (e.g., `agent2`, `test-env4`, `agent-qt-3`).

If no numbered environments exist, generate a default name:

```powershell
$suffix = -join ((0..9) + ('a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z') | Get-Random -Count 6)
$suggestedName = "agent-qt-$suffix"
```

#### 1c. Ask the user

**If a default environment was found**, present the user with choices:

1. **Use the current environment `<defaultEnvName>`** — re-provision/update the existing
   environment (first choice, include the environment name in the label)
2. **Create a new environment `<suggestedName>`** — use the suggested new name from 1b
3. **Enter a different name** — the user provides their own name

For example:

> Do you want to `azd up` the current environment **`agent-qt-2`**, or create a new one?

**If no default environment was found**, present the user with choices:

1. **Use the suggested name `<suggestedName>`** — use the name generated in 1b
2. **Enter a different name** — the user provides their own name

- If the user **provides a different name**, use their name instead.
- Environment names must be **lowercase alphanumeric and hyphens only**, max 64 characters.

The resource group will be `rg-<envName>`.

### 1½. Check for existing AI project (shortcut)

After resolving the environment name, check whether the selected environment already has
`AZURE_EXISTING_AIPROJECT_RESOURCE_ID` set:

```powershell
$existingProject = azd env get-value AZURE_EXISTING_AIPROJECT_RESOURCE_ID --environment $envName 2>$null
```

If the value is **non-empty**, the environment is pre-configured to use an existing AI project.
Print the **short-path** steps overview and **jump directly to Step 9 (`azd up`)**:

> **Up Skill — Steps Overview** (environment: `<envName>`, existing AI project)
>
> 1. ✅ Choose environment name
> 2–8. ⏭️ Skipped (existing AI project detected)
> 9. Run `azd up`
> 10. Retrieve the app endpoint
> 11. Health-check the app
> 12. Report results

If the value is **empty or not set**, print the **full-path** steps overview and continue
to Step 2:

> **Up Skill — Steps Overview** (environment: `<envName>`)
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

### 2. Resolve subscription

Auto-detect the default Azure Subscription ID using this priority order (use the first one found):

1. Environment variable `AZURE_SUBSCRIPTION_ID`
2. `azd config get defaults.subscription` (may return empty)
3. `az account show --query id -o tsv` (current Azure CLI login)

Present the user with **2 choices**:

1. **Use the detected subscription** — show the subscription ID (and name if available via
   `az account show --query "{id:id, name:name}" -o json`) as the default choice
2. **Enter a different subscription** — prompt the user to input a subscription ID

If no subscription was detected, skip choice 1 and ask the user to provide one directly.

Show the resolved subscription to the user for confirmation before proceeding.

### 3. Check RBAC permissions (prerequisite)

Verify the user has sufficient permissions to create role assignments on the subscription,
which is required for provisioning. The user needs **Owner** or **User Access Administrator**
— either assigned directly or inherited through a group membership.

#### 3a. Check direct role assignments

```powershell
$principalId = az ad signed-in-user show --query id -o tsv
$subScope = "/subscriptions/<subscriptionId>"
$roles = az role assignment list --assignee $principalId --scope $subScope --query "[].roleDefinitionName" -o json | ConvertFrom-Json
```

Check if `$roles` contains `Owner` or `User Access Administrator`.

- If **yes**, proceed to Step 4.
- If **no**, continue to 3b to check group-based assignments.

#### 3b. Check group-based role assignments

The user may hold the required role through a group membership. Query the user's group
memberships and check whether any of those groups have the required roles on the subscription.

```powershell
$groupIds = az ad signed-in-user get-member-of --query "[].id" -o json | ConvertFrom-Json
```

If `$groupIds` is non-empty, check role assignments for each group on the subscription:

```powershell
$groupRoles = @()
foreach ($gid in $groupIds) {
    $gr = az role assignment list --assignee $gid --scope $subScope --query "[].roleDefinitionName" -o json 2>$null | ConvertFrom-Json
    if ($gr) { $groupRoles += $gr }
}
```

Check if `$groupRoles` contains `Owner` or `User Access Administrator`.

- If **yes**, proceed to Step 4.
- If **no**, report the issue:
  - Show the **subscription name and ID** that failed the check
  - Show the user's current roles on the subscription
  - Explain that `azd up` will fail because the deployment creates `Microsoft.Authorization/roleAssignments`
  - Present **3 choices**:
    1. **"I just added the role — re-check"** → Re-run the RBAC check on the same subscription
    2. **"Use a different subscription"** → Prompt the user for a new subscription ID, then go back to Step 3
    3. **"Exit"** → Stop the skill

### 4. Resolve region

Check environment variable `AZURE_LOCATION` first. If not set,
ask the user — must be one of: `eastus`, `eastus2`, `swedencentral`, `westus`, `westus3`.
Default to `eastus` if the user has no preference.

Show the resolved region to the user for confirmation before proceeding.

### 5. Check agent model quota (prerequisite)

Before provisioning, verify the default agent model has sufficient quota in the selected region.

**Default model:** `gpt-5-mini` | **SKU:** `GlobalStandard` | **Required capacity:** 80

#### 5a. Query quota and model availability

```powershell
$usage = az cognitiveservices usage list --location <region> --subscription <subscriptionId> -o json | ConvertFrom-Json
$modelList = az cognitiveservices model list --location <region> --subscription <subscriptionId> -o json | ConvertFrom-Json
```

Cache both `$usage` and `$modelList` — they are reused in Step 7 for embedding checks.

#### 5b. Check default agent model quota

```powershell
$defaultUsageName = "OpenAI.GlobalStandard.gpt-5-mini"
$entry = $usage | Where-Object { $_.name.value -eq $defaultUsageName }
```

If the entry exists, compute `available = limit - currentValue`.

- If `available >= 80`, the default model has enough quota — **skip to Step 6**.
- If the entry is **missing**, the model/SKU is not available in this region — continue to 5c.
- If `available < 80`, quota is insufficient — continue to 5c.

Report the finding to the user (e.g., "gpt-5-mini has 40/80 quota available — insufficient").

#### 5c. Find alternative agent models

From the quota usage list, find all GPT entries with `Global` or `GlobalStandard` SKUs
that have sufficient available quota:

```powershell
$gptEntries = $usage | Where-Object {
    $_.name.value -match '^OpenAI\.(Global|GlobalStandard)\.gpt-' -and
    ($_.limit - $_.currentValue) -ge 80
}
```

For each candidate, **cross-reference with `$modelList`** to confirm the model is actually
deployable (exists with format `OpenAI` and is not retired). Discard any candidate not
confirmed by the model list.

#### 5d. Rank agent model candidates

Use this preference order (higher is better):

1. `gpt-5.2`
2. `gpt-5.2-mini`
3. `gpt-5.1`
4. `gpt-5.1-mini`
5. `gpt-5`
6. `gpt-5-mini`
7. `gpt-4.1`
8. `gpt-4.1-mini`
9. `gpt-4o`
10. `gpt-4o-mini`

Within the same model name, prefer `GlobalStandard` over `Global`.

#### 5e. Suggest the best alternative

Present the top candidate to the user with:

- Model name
- SKU type (`Global` or `GlobalStandard`)
- Available quota

Ask for confirmation before proceeding.

#### 5f. Resolve agent model version

For the selected model, look up the version from the model list:

```powershell
$match = $modelList | Where-Object {
    $_.model.name -eq '<selectedModel>' -and
    $_.model.format -eq 'OpenAI'
}
```

If multiple versions exist, prefer the **newest Generally Available** version.
If only preview versions exist, warn the user before proceeding.

Store the resolved agent model name, SKU, and version for use in Step 8.

#### 5g. No agent model quota available

If **no** GPT model in `Global` or `GlobalStandard` has sufficient quota (≥ 80) in the
selected region, stop and report the issue. Suggest the user try a different region or
request a quota increase.

### 6. Ask about Azure AI Search

Ask the user whether they want to enable **Azure AI Search** for this deployment.
Azure AI Search adds vector search and RAG capabilities but requires an embedding model
and an additional Azure Search resource.

- Default is **No** (matches `USE_AZURE_AI_SEARCH_SERVICE=false` in the template).
- If the user says **Yes**, proceed to Step 7 to check embedding model quota.
- If the user says **No**, skip Step 7 entirely and proceed to Step 8.

### 7. Check embedding model quota (if AI Search enabled)

Only run this step if the user opted into Azure AI Search in Step 6.

**Default model:** `text-embedding-3-small` | **SKU:** `Standard` | **Required capacity:** 50

#### 7a. Check default embedding model quota

Reuse the `$usage` and `$modelList` cached from Step 5a.

```powershell
$embedUsageName = "OpenAI.Standard.text-embedding-3-small"
$embedEntry = $usage | Where-Object { $_.name.value -eq $embedUsageName }
```

If the entry exists, compute `available = limit - currentValue`.

- If `available >= 50`, the default embedding model has enough quota — **skip to Step 8**.
- If the entry is **missing** or `available < 50` — continue to 7b.

Report the finding to the user.

#### 7b. Find alternative embedding models

From the quota usage list, find all embedding entries with sufficient quota:

```powershell
$embedEntries = $usage | Where-Object {
    $_.name.value -match '^OpenAI\.(Global|GlobalStandard|Standard)\.text-embedding-' -and
    ($_.limit - $_.currentValue) -ge 50
}
```

Cross-reference with `$modelList` to confirm each candidate is deployable.

#### 7c. Rank embedding model candidates

Use this preference order (higher is better):

1. `text-embedding-3-large`
2. `text-embedding-3-small`
3. `text-embedding-ada-002`

Within the same model name, prefer `Standard` over `GlobalStandard` over `Global`.

#### 7d. Suggest the best alternative

Present the top candidate to the user with model name, SKU, and available quota.
Ask for confirmation before proceeding.

#### 7e. Resolve embedding model version

For the selected model, look up the version from `$modelList`:

```powershell
$embedMatch = $modelList | Where-Object {
    $_.model.name -eq '<selectedEmbedModel>' -and
    $_.model.format -eq 'OpenAI'
}
```

Prefer the **newest Generally Available** version.

Store the resolved embedding model name, SKU, version, and dimensions for use in Step 8.

**Note:** If using `text-embedding-3-large`, set dimensions to `1536`.
If using `text-embedding-3-small`, set dimensions to `1536`.
If using `text-embedding-ada-002`, set dimensions to `1536`.

#### 7f. No embedding model quota available

If **no** embedding model has sufficient quota (≥ 50) in the selected region, warn the
user that AI Search cannot be enabled. Offer to proceed without AI Search (set
`USE_AZURE_AI_SEARCH_SERVICE=false`) or stop.

### 8. Create the azd environment and set overrides

#### 8a. Create the environment

If the user chose an **existing** environment in Step 1c, skip creation — the environment
already exists. Proceed to 8b.

If the user chose a **new** environment name, create it:

```powershell
azd env new $envName --no-prompt
```

If this fails, stop and report the error.

#### 8b. Set subscription, region, and model overrides

```powershell
azd env set AZURE_SUBSCRIPTION_ID <subscriptionId> --environment $envName --no-prompt
azd env set AZURE_LOCATION <region> --environment $envName --no-prompt
```

Use the values collected in Steps 2 and 4.

If Step 5 determined an alternative agent model, apply the agent model overrides:

```powershell
azd env set AZURE_AI_AGENT_MODEL_NAME "<selectedAgentModel>" --environment $envName --no-prompt
azd env set AZURE_AI_AGENT_DEPLOYMENT_SKU "<selectedAgentSku>" --environment $envName --no-prompt
azd env set AZURE_AI_AGENT_MODEL_VERSION "<selectedAgentVersion>" --environment $envName --no-prompt
azd env set AZURE_AI_AGENT_MODEL_FORMAT "OpenAI" --environment $envName --no-prompt
azd env set AZURE_AI_AGENT_DEPLOYMENT_CAPACITY "80" --environment $envName --no-prompt
```

If the user enabled AI Search (Step 6), set:

```powershell
azd env set USE_AZURE_AI_SEARCH_SERVICE "true" --environment $envName --no-prompt
```

If Step 7 determined an alternative embedding model, apply the embedding model overrides:

```powershell
azd env set AZURE_AI_EMBED_MODEL_NAME "<selectedEmbedModel>" --environment $envName --no-prompt
azd env set AZURE_AI_EMBED_DEPLOYMENT_NAME "<selectedEmbedModel>" --environment $envName --no-prompt
azd env set AZURE_AI_EMBED_DEPLOYMENT_SKU "<selectedEmbedSku>" --environment $envName --no-prompt
azd env set AZURE_AI_EMBED_MODEL_VERSION "<selectedEmbedVersion>" --environment $envName --no-prompt
azd env set AZURE_AI_EMBED_DIMENSIONS "<dimensions>" --environment $envName --no-prompt
```

### 9. Run `azd up`

This provisions infrastructure and deploys the app. It typically takes 10–15 minutes.

Run with `mode="async"` so the user sees live streaming output:

```powershell
azd up --environment $envName --no-prompt
```

After launching, **poll with short delays** — call `read_powershell` with a **15–20 second
delay** on each turn, and show the user whatever new output appeared. Repeat in a loop
(one `read_powershell` per response turn) until the command completes. This gives the
user a near-real-time view of provisioning progress. Do NOT use 120-second delays.

- If `azd up` **fails**, report the error and offer to run `azd down --environment $envName --force --purge --no-prompt` (also `mode="async"`) to clean up.
- If `azd up` **succeeds**, proceed to the health check.

### 10. Retrieve the app endpoint

After `azd up` succeeds, get the deployed app URL:

```powershell
$serviceUri = azd env get-value SERVICE_API_URI --environment $envName
```

If that returns empty, fall back to reading `.azure/<envName>/.env` and parsing the `SERVICE_API_URI` line.

### 11. Health-check the app

Try up to 5 times (15 seconds apart) to reach the app:

```powershell
$healthy = $false
for ($i = 1; $i -le 5; $i++) {
    try {
        $resp = Invoke-WebRequest -Uri $serviceUri -UseBasicParsing -TimeoutSec 30 -ErrorAction Stop
        if ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 400) {
            $healthy = $true
            Write-Host "Attempt $i - HTTP $($resp.StatusCode) - App is running!"
            break
        }
    } catch {
        Write-Host "Attempt $i - $($_.Exception.Message)"
    }
    if ($i -lt 5) { Start-Sleep -Seconds 15 }
}
```

### 12. Report results

Print a summary with:

| Field            | Value                        |
|------------------|------------------------------|
| Subscription     | `<subscriptionId>`           |
| Environment      | `$envName`                   |
| Resource Group   | `rg-$envName`                |
| Region           | `<region>`                   |
| Agent Model      | `<agentModel>` (`<agentSku>`)  |
| AI Search        | Enabled / Disabled           |
| Embedding Model  | `<embedModel>` (`<embedSku>`) or N/A |
| App URL          | `$serviceUri`                |
| Status           | ✅ PASS or ❌ FAIL            |

- **PASS** = `azd up` succeeded AND health check returned HTTP 2xx/3xx.
- **FAIL** = either `azd up` failed or the app did not respond after 5 retries.

If the test **failed**, ask the user whether to tear down with:
```powershell
azd down --environment $envName --force --purge --no-prompt
```

If the test **passed**, congratulate and remind them the environment is still running (costs apply) and offer to tear it down.

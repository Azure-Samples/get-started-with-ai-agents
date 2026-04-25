---
name: deploy
description: Creates an azd environment, checks prerequisites (RBAC, model quota), provisions infrastructure via `azd up`, and health-checks the deployed app.
---

# Deploy Skill

## Goal

Provision a fresh Azure environment end-to-end and verify the app starts successfully.

## Before starting

When the skill is triggered, **always re-read this SKILL.md file** from disk before
executing, in case it has been updated since the last run.

Then **print the full list of steps** so the user knows what to expect:

> **Deploy Skill — Steps Overview**
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

Then proceed to Step 1.

## Terminal usage

All shell commands in this skill **must** be run using the `powershell` tool with
`mode="sync"`. Use a short `initial_wait` (30 seconds) for quick commands like
`az account show`, `az ad signed-in-user show`, `az role assignment list`,
`azd env list`, `azd env new`, and `azd env set`. Use a long `initial_wait`
(600 seconds) for `azd up` and `azd down`.

**Do NOT** fall back to async/background terminals to capture output.
Run the command with `mode="sync"` and read the output directly from the
tool response. If the command takes longer than `initial_wait`, you will be
notified when it completes — use `read_powershell` to retrieve the output.

Chain short related commands with `&&` or `;` into a single `powershell` call
when they have no branching logic between them.

## Steps

### 1. Resolve subscription

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

### 2. Check RBAC permissions (prerequisite)

Verify the user has sufficient permissions to create role assignments on the subscription,
which is required for provisioning. The user needs **Owner** or **User Access Administrator**
— either assigned directly or inherited through a group membership.

#### 2a. Check direct role assignments

```powershell
$principalId = az ad signed-in-user show --query id -o tsv
$subScope = "/subscriptions/<subscriptionId>"
$roles = az role assignment list --assignee $principalId --scope $subScope --query "[].roleDefinitionName" -o json | ConvertFrom-Json
```

Check if `$roles` contains `Owner` or `User Access Administrator`.

- If **yes**, proceed to Step 3.
- If **no**, continue to 2b to check group-based assignments.

#### 2b. Check group-based role assignments

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

- If **yes**, proceed to Step 3.
- If **no**, report the issue:
  - Show the **subscription name and ID** that failed the check
  - Show the user's current roles on the subscription
  - Explain that `azd up` will fail because the deployment creates `Microsoft.Authorization/roleAssignments`
  - Present **3 choices**:
    1. **"I just added the role — re-check"** → Re-run the RBAC check on the same subscription
    2. **"Use a different subscription"** → Prompt the user for a new subscription ID, then go back to Step 2
    3. **"Exit"** → Stop the skill

### 3. Resolve region

Check environment variable `AZURE_LOCATION` first. If not set,
ask the user — must be one of: `eastus`, `eastus2`, `swedencentral`, `westus`, `westus3`.
Default to `eastus` if the user has no preference.

Show the resolved region to the user for confirmation before proceeding.

### 4. Check chat model quota (prerequisite)

Before provisioning, verify the default chat model has sufficient quota in the selected region.

**Default model:** `gpt-5-mini` | **SKU:** `GlobalStandard` | **Required capacity:** 80

#### 4a. Query quota and model availability

```powershell
$usage = az cognitiveservices usage list --location <region> --subscription <subscriptionId> -o json | ConvertFrom-Json
$modelList = az cognitiveservices model list --location <region> --subscription <subscriptionId> -o json | ConvertFrom-Json
```

Cache both `$usage` and `$modelList` — they are reused in Step 6 for embedding checks.

#### 4b. Check default chat model quota

```powershell
$defaultUsageName = "OpenAI.GlobalStandard.gpt-5-mini"
$entry = $usage | Where-Object { $_.name.value -eq $defaultUsageName }
```

If the entry exists, compute `available = limit - currentValue`.

- If `available >= 80`, the default model has enough quota — **skip to Step 5**.
- If the entry is **missing**, the model/SKU is not available in this region — continue to 4c.
- If `available < 80`, quota is insufficient — continue to 4c.

Report the finding to the user (e.g., "gpt-5-mini has 40/80 quota available — insufficient").

#### 4c. Find alternative chat models

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

#### 4d. Rank chat model candidates

Use this preference order (higher is better):

1. `gpt-5`
2. `gpt-4.1`
3. `gpt-4o`
4. `gpt-5-mini`
5. `gpt-4.1-mini`
6. `gpt-4o-mini`

Within the same model name, prefer `GlobalStandard` over `Global`.

#### 4e. Suggest the best alternative

Present the top candidate to the user with:

- Model name
- SKU type (`Global` or `GlobalStandard`)
- Available quota

Ask for confirmation before proceeding.

#### 4f. Resolve chat model version

For the selected model, look up the version from the model list:

```powershell
$match = $modelList | Where-Object {
    $_.model.name -eq '<selectedModel>' -and
    $_.model.format -eq 'OpenAI'
}
```

If multiple versions exist, prefer the **newest Generally Available** version.
If only preview versions exist, warn the user before proceeding.

Store the resolved chat model name, SKU, and version for use in Step 8.

#### 4g. No chat model quota available

If **no** GPT model in `Global` or `GlobalStandard` has sufficient quota (≥ 80) in the
selected region, stop and report the issue. Suggest the user try a different region or
request a quota increase.

### 5. Ask about Azure AI Search

Ask the user whether they want to enable **Azure AI Search** for this deployment.
Azure AI Search adds vector search and RAG capabilities but requires an embedding model
and an additional Azure Search resource.

- Default is **No** (matches `USE_AZURE_AI_SEARCH_SERVICE=false` in the template).
- If the user says **Yes**, proceed to Step 6 to check embedding model quota.
- If the user says **No**, skip Step 6 entirely and proceed to Step 7.

### 6. Check embedding model quota (if AI Search enabled)

Only run this step if the user opted into Azure AI Search in Step 5.

**Default model:** `text-embedding-3-small` | **SKU:** `Standard` | **Required capacity:** 50

#### 6a. Check default embedding model quota

Reuse the `$usage` and `$modelList` cached from Step 4a.

```powershell
$embedUsageName = "OpenAI.Standard.text-embedding-3-small"
$embedEntry = $usage | Where-Object { $_.name.value -eq $embedUsageName }
```

If the entry exists, compute `available = limit - currentValue`.

- If `available >= 50`, the default embedding model has enough quota — **skip to Step 7**.
- If the entry is **missing** or `available < 50` — continue to 6b.

Report the finding to the user.

#### 6b. Find alternative embedding models

From the quota usage list, find all embedding entries with sufficient quota:

```powershell
$embedEntries = $usage | Where-Object {
    $_.name.value -match '^OpenAI\.(Global|GlobalStandard|Standard)\.text-embedding-' -and
    ($_.limit - $_.currentValue) -ge 50
}
```

Cross-reference with `$modelList` to confirm each candidate is deployable.

#### 6c. Rank embedding model candidates

Use this preference order (higher is better):

1. `text-embedding-3-large`
2. `text-embedding-3-small`
3. `text-embedding-ada-002`

Within the same model name, prefer `Standard` over `GlobalStandard` over `Global`.

#### 6d. Suggest the best alternative

Present the top candidate to the user with model name, SKU, and available quota.
Ask for confirmation before proceeding.

#### 6e. Resolve embedding model version

For the selected model, look up the version from `$modelList`:

```powershell
$embedMatch = $modelList | Where-Object {
    $_.model.name -eq '<selectedEmbedModel>' -and
    $_.model.format -eq 'OpenAI'
}
```

Prefer the **newest Generally Available** version.

Store the resolved embedding model name, SKU, version, and dimensions for use in Step 9.

**Note:** If using `text-embedding-3-large`, set dimensions to `1536`.
If using `text-embedding-3-small`, set dimensions to `1536`.
If using `text-embedding-ada-002`, set dimensions to `1536`.

#### 6f. No embedding model quota available

If **no** embedding model has sufficient quota (≥ 50) in the selected region, warn the
user that AI Search cannot be enabled. Offer to proceed without AI Search (set
`USE_AZURE_AI_SEARCH_SERVICE=false`) or stop.

### 7. Choose environment name

Look up the user's existing azd environments to suggest a smart name:

```powershell
$existingEnvs = azd env list -o json 2>$null | ConvertFrom-Json
```

#### 7a. Generate a suggested name

Scan `$existingEnvs` for names matching the pattern `<prefix><number>` (e.g., `myapp1`,
`test-env3`, `howie-qt-2`). If found, take the one with the **highest number** and suggest
the next increment (e.g., `myapp2`, `test-env4`, `howie-qt-3`).

If no numbered environments exist, generate a default name:

```powershell
$suffix = -join ((0..9) + ('a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z') | Get-Random -Count 6)
$suggestedName = "howie-qt-$suffix"
```

#### 7b. Confirm with the user

Present the suggested name and ask if they are happy with it. For example:

> Suggested environment name: `myapp3`
> Is this name OK, or would you like to use a different name?

- If the user **accepts**, use the suggested name.
- If the user **provides a different name**, use their name instead.
- Environment names must be **lowercase alphanumeric and hyphens only**, max 64 characters.

The resource group will be `rg-<envName>`.

### 8. Create the azd environment

```powershell
azd env new $envName --no-prompt
```

If this fails, stop and report the error.

### 9. Set subscription, region, and model overrides

```powershell
azd env set AZURE_SUBSCRIPTION_ID <subscriptionId> --environment $envName --no-prompt
azd env set AZURE_LOCATION <region> --environment $envName --no-prompt
```

Use the values collected in Steps 1 and 3.

If Step 4 determined an alternative chat model, apply the chat model overrides:

```powershell
azd env set AZURE_AI_AGENT_MODEL_NAME "<selectedChatModel>" --environment $envName --no-prompt
azd env set AZURE_AI_AGENT_DEPLOYMENT_SKU "<selectedChatSku>" --environment $envName --no-prompt
azd env set AZURE_AI_AGENT_MODEL_VERSION "<selectedChatVersion>" --environment $envName --no-prompt
```

If the user enabled AI Search (Step 5), set:

```powershell
azd env set USE_AZURE_AI_SEARCH_SERVICE "true" --environment $envName --no-prompt
```

If Step 6 determined an alternative embedding model, apply the embedding model overrides:

```powershell
azd env set AZURE_AI_EMBED_MODEL_NAME "<selectedEmbedModel>" --environment $envName --no-prompt
azd env set AZURE_AI_EMBED_DEPLOYMENT_NAME "<selectedEmbedModel>" --environment $envName --no-prompt
azd env set AZURE_AI_EMBED_DEPLOYMENT_SKU "<selectedEmbedSku>" --environment $envName --no-prompt
azd env set AZURE_AI_EMBED_MODEL_VERSION "<selectedEmbedVersion>" --environment $envName --no-prompt
azd env set AZURE_AI_EMBED_DIMENSIONS "<dimensions>" --environment $envName --no-prompt
```

### 10. Run `azd up`

This provisions infrastructure and deploys the app. It typically takes 10–15 minutes.

```powershell
azd up --environment $envName --no-prompt
```

- If `azd up` **fails**, report the error and offer to run `azd down --environment $envName --force --purge --no-prompt` to clean up.
- If `azd up` **succeeds**, proceed to the health check.

### 11. Retrieve the app endpoint

After `azd up` succeeds, get the deployed app URL:

```powershell
$serviceUri = azd env get-value SERVICE_API_URI --environment $envName
```

If that returns empty, fall back to reading `.azure/<envName>/.env` and parsing the `SERVICE_API_URI` line.

### 12. Health-check the app

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

### 13. Report results

Print a summary with:

| Field            | Value                        |
|------------------|------------------------------|
| Subscription     | `<subscriptionId>`           |
| Environment      | `$envName`                   |
| Resource Group   | `rg-$envName`                |
| Region           | `<region>`                   |
| Chat Model       | `<chatModel>` (`<chatSku>`)  |
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

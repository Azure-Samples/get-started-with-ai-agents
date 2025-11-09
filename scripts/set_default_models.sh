#!/bin/bash

set -e

# --- Check Required Environment Variables ---
SubscriptionId="${AZURE_SUBSCRIPTION_ID}"
Location="${AZURE_LOCATION}"

Errors=0

if [ -z "$SubscriptionId" ]; then
    echo "❌ ERROR: Missing AZURE_SUBSCRIPTION_ID" >&2
    Errors=$((Errors + 1))
fi

if [ -z "$Location" ]; then
    echo "❌ ERROR: Missing AZURE_LOCATION" >&2
    Errors=$((Errors + 1))
fi

if [ "$Errors" -gt 0 ]; then
    exit 1
fi

# --- Default Values ---
declare -A defaultEnvVars=(
    [AZURE_AI_EMBED_DEPLOYMENT_NAME]="text-embedding-3-small"
    [AZURE_AI_EMBED_MODEL_NAME]="text-embedding-3-small"
    [AZURE_AI_EMBED_MODEL_FORMAT]="OpenAI"
    [AZURE_AI_EMBED_MODEL_VERSION]="1"
    [AZURE_AI_EMBED_DEPLOYMENT_SKU]="Standard"
    [AZURE_AI_EMBED_DEPLOYMENT_CAPACITY]="50"
    [AZURE_AI_AGENT_DEPLOYMENT_NAME]="gpt-5-mini"
    [AZURE_AI_AGENT_MODEL_NAME]="gpt-5-mini"
    [AZURE_AI_AGENT_MODEL_VERSION]="2024-07-18"
    [AZURE_AI_AGENT_MODEL_FORMAT]="OpenAI"
    [AZURE_AI_AGENT_DEPLOYMENT_SKU]="GlobalStandard"
    [AZURE_AI_AGENT_DEPLOYMENT_CAPACITY]="80"
)

# --- Set Env Vars and azd env ---
declare -A envVars
for key in "${!defaultEnvVars[@]}"; do
    val="${!key}"
    if [ -z "$val" ]; then
        val="${defaultEnvVars[$key]}"
    fi
    envVars[$key]="$val"
    azd env set "$key" "$val"
done

# --- If we do not use existing AI Project, we don't deploy models, so skip validation ---
resourceId="${AZURE_EXISTING_AIPROJECT_RESOURCE_ID}"
if [ -n "$resourceId" ]; then
    echo "✅ AZURE_EXISTING_AIPROJECT_RESOURCE_ID is set, skipping model deployment validation."
    exit 0
fi

# --- Build Chat Deployment ---
chatDeployment_name="${envVars[AZURE_AI_AGENT_DEPLOYMENT_NAME]}"
chatDeployment_model_name="${envVars[AZURE_AI_AGENT_MODEL_NAME]}"
chatDeployment_model_version="${envVars[AZURE_AI_AGENT_MODEL_VERSION]}"
chatDeployment_model_format="${envVars[AZURE_AI_AGENT_MODEL_FORMAT]}"
chatDeployment_sku_name="${envVars[AZURE_AI_AGENT_DEPLOYMENT_SKU]}"
chatDeployment_capacity="${envVars[AZURE_AI_AGENT_DEPLOYMENT_CAPACITY]}"
chatDeployment_capacity_env="AZURE_AI_AGENT_DEPLOYMENT_CAPACITY"

aiModelDeployments=(
    "$chatDeployment_name|$chatDeployment_model_name|$chatDeployment_model_version|$chatDeployment_model_format|$chatDeployment_sku_name|$chatDeployment_capacity|$chatDeployment_capacity_env"
)

# --- Optional Embed Deployment ---
if [ "$USE_AZURE_AI_SEARCH_SERVICE" == "true" ]; then
    embedDeployment_name="${envVars[AZURE_AI_EMBED_DEPLOYMENT_NAME]}"
    embedDeployment_model_name="${envVars[AZURE_AI_EMBED_MODEL_NAME]}"
    embedDeployment_model_version="${envVars[AZURE_AI_EMBED_MODEL_VERSION]}"
    embedDeployment_model_format="${envVars[AZURE_AI_EMBED_MODEL_FORMAT]}"
    embedDeployment_sku_name="${envVars[AZURE_AI_EMBED_DEPLOYMENT_SKU]}"
    embedDeployment_capacity="${envVars[AZURE_AI_EMBED_DEPLOYMENT_CAPACITY]}"
    embedDeployment_capacity_env="AZURE_AI_EMBED_DEPLOYMENT_CAPACITY"

    aiModelDeployments+=(
        "$embedDeployment_name|$embedDeployment_model_name|$embedDeployment_model_version|$embedDeployment_model_format|$embedDeployment_sku_name|$embedDeployment_capacity|$embedDeployment_capacity_env"
    )
fi

# --- Set Subscription ---
az account set --subscription "$SubscriptionId"
echo "🎯 Active Subscription: $(az account show --query '[name, id]' --output tsv)"

QuotaAvailable=true

# --- Validate Quota ---
for entry in "${aiModelDeployments[@]}"; do
    IFS="|" read -r name model model_version format type capacity capacity_env_var_name <<< "$entry"
    echo "🔍 Validating model deployment: $name ..."
    ./scripts/resolve_model_quota.sh \
        -Location "$Location" \
        -Model "$model" \
        -Format "$format" \
        -Capacity "$capacity" \
        -CapacityEnvVarName "$capacity_env_var_name" \
        -DeploymentType "$type"

    if [ $? -ne 0 ]; then
        echo "❌ ERROR: Quota validation failed for model deployment: $name" >&2
        QuotaAvailable=false
    fi
done

# --- Final Check ---
if [ "$QuotaAvailable" != "true" ]; then
    exit 1
else
    echo "✅ All model deployments passed quota validation successfully."
    exit 0
fi
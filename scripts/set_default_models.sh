#!/bin/bash

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -SubscriptionId) SubscriptionId="$2"; shift ;;
        -Location) Location="$2"; shift ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

    
# Validate required parameters
MissingParams=()
[ -z "$SubscriptionId" ] && MissingParams+=("subscription")
[ -z "$Location" ] && MissingParams+=("location")

if [ ${#MissingParams[@]} -gt 0 ]; then
    echo "❌ ERROR: Missing required parameters: ${MissingParams[*]}"
    echo "Usage: ./set_default_models.sh -SubscriptionId <SUBSCRIPTION_ID> -Location <LOCATION>"
    exit 1
fi



# Default environment variables
declare -A defaultEnvVars=(
    [AZURE_AI_EMBED_DEPLOYMENT_NAME]="text-embedding-3-small"
    [AZURE_AI_EMBED_MODEL_NAME]="text-embedding-3-small"
    [AZURE_AI_EMBED_MODEL_FORMAT]="OpenAI"
    [AZURE_AI_EMBED_MODEL_VERSION]="1"
    [AZURE_AI_EMBED_DEPLOYMENT_SKU]="Standard"
    [AZURE_AI_EMBED_DEPLOYMENT_CAPACITY]="50"
    [AZURE_AI_AGENT_DEPLOYMENT_NAME]="gpt-4o-mini"
    [AZURE_AI_AGENT_MODEL_NAME]="gpt-4o-mini"
    [AZURE_AI_AGENT_MODEL_VERSION]="2024-07-18"
    [AZURE_AI_AGENT_MODEL_FORMAT]="OpenAI"
    [AZURE_AI_AGENT_DEPLOYMENT_SKU]="GlobalStandard"
    [AZURE_AI_AGENT_DEPLOYMENT_CAPACITY]="80"
)

# Set environment variables
for key in "${!defaultEnvVars[@]}"; do
    val="${!key}"
    if [ -z "$val" ]; then
        val="${defaultEnvVars[$key]}"
        export $key="$val"
    fi
    azd env set "$key" "$val"
done

# Build chat deployment
chatDeployment=(
    "$AZURE_AI_AGENT_DEPLOYMENT_NAME"
    "$AZURE_AI_AGENT_MODEL_NAME"
    "$AZURE_AI_AGENT_MODEL_VERSION"
    "$AZURE_AI_AGENT_MODEL_FORMAT"
    "$AZURE_AI_AGENT_DEPLOYMENT_SKU"
    "$AZURE_AI_AGENT_DEPLOYMENT_CAPACITY"
    "AZURE_AI_AGENT_DEPLOYMENT_CAPACITY"
)

aiModelDeployments=("${chatDeployment[@]}")


# Optionally add embed deployment
if [[ "${USE_AZURE_AI_SEARCH_SERVICE,,}" == "true" ]]; then
    embedDeployment=(
        "$AZURE_AI_EMBED_DEPLOYMENT_NAME"
        "$AZURE_AI_EMBED_MODEL_NAME"
        "$AZURE_AI_EMBED_MODEL_VERSION"
        "$AZURE_AI_EMBED_MODEL_FORMAT"
        "$AZURE_AI_EMBED_DEPLOYMENT_SKU"
        "$AZURE_AI_EMBED_DEPLOYMENT_CAPACITY"
        "AZURE_AI_EMBED_DEPLOYMENT_CAPACITY"
    )
    aiModelDeployments+=("${embedDeployment[@]}")
fi
# Set subscription
az account set --subscription "$SubscriptionId"
echo "🎯 Active Subscription: $(az account show --query '[name, id]' --output tsv)"


# Validate quota
QuotaAvailable=true
for ((i=0; i<${#aiModelDeployments[@]}; i+=7)); do
    name="${aiModelDeployments[i]}"
    model="${aiModelDeployments[i+1]}"
    version="${aiModelDeployments[i+2]}"
    format="${aiModelDeployments[i+3]}"
    sku="${aiModelDeployments[i+4]}"
    ideal_capacity="${aiModelDeployments[i+5]}"
    capacity_env="${aiModelDeployments[i+6]}"
    min_capacity=30

    echo "🔍 Validating model deployment: $name ..."
    ./scripts/resolve_model_quota.sh -Location "$Location" -Model "$model" -IdealCapacity "$ideal_capacity" -MinCapacity "$min_capacity" -CapacityEnvVarName "$capacity_env" -DeploymentType "$sku"
    if [ $? -ne 0 ]; then
        echo "❌ ERROR: Quota validation failed for model deployment: $name"
        QuotaAvailable=false
    fi
done


if [ "$QuotaAvailable" = false ]; then
    exit 1
else
    echo "✅ All model deployments passed quota validation successfully."
    exit 0
fi


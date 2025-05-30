#!/bin/bash

# Initialize variables
Location=""
Model=""
DeploymentType="Standard"
CapacityEnvVarName=""
IdealCapacity=""
MinCapacity=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        -Location)
            Location="$2"
            shift 2
            ;;
        -Model)
            Model="$2"
            shift 2
            ;;
        -DeploymentType)
            DeploymentType="$2"
            shift 2
            ;;
        -CapacityEnvVarName)
            CapacityEnvVarName="$2"
            shift 2
            ;;
        -IdealCapacity)
            IdealCapacity="$2"
            shift 2
            ;;
        -MinCapacity)
            MinCapacity="$2"
            shift 2
            ;;
        *)
            echo "❌ ERROR: Unknown parameter: $1"
            exit 1
            ;;
    esac
done

# Check for missing required parameters
MissingParams=()
[[ -z "$Location" ]] && MissingParams+=("location")
[[ -z "$Model" ]] && MissingParams+=("model")
[[ -z "$IdealCapacity" ]] && MissingParams+=("capacity")
[[ -z "$DeploymentType" ]] && MissingParams+=("deployment-type")

if [[ ${#MissingParams[@]} -gt 0 ]]; then
    echo "❌ ERROR: Missing required parameters: ${MissingParams[*]}"
    echo "Usage: ./resolve_model_quota.sh -Location <Location> -Model <Model> -IdealCapacity <CAPACITY> -MinCapacity <CAPACITY> -CapacityEnvVarName <ENV_VAR_NAME> [-DeploymentType <DeploymentType>]"
    exit 1
fi

if [[ "$DeploymentType" != "Standard" && "$DeploymentType" != "GlobalStandard" ]]; then
    echo "❌ ERROR: Invalid deployment type: $DeploymentType. Allowed values are 'Standard' or 'GlobalStandard'."
    exit 1
fi

ModelType="OpenAI.$DeploymentType.$Model"

echo "🔍 Checking quota for $ModelType in $Location ..."

ModelInfo=$(az cognitiveservices usage list --location "$Location" --query "[?name.value=='$ModelType']" --output json | tr '[:upper:]' '[:lower:]')

if [ -z "$ModelInfo" ]; then
    echo "❌ ERROR: No quota information found for model: $Model in location: $Location for model type: $ModelType."
    exit 1
fi

if [ -n "$ModelInfo" ]; then
    CurrentValue=$(echo "$ModelInfo" | awk -F': ' '/"currentvalue"/ {print $2}' | tr -d ',' | tr -d ' ')
    Limit=$(echo "$ModelInfo" | awk -F': ' '/"limit"/ {print $2}' | tr -d ',' | tr -d ' ')

    CurrentValue=${CurrentValue:-0}
    Limit=${Limit:-0}

    CurrentValue=$(echo "$CurrentValue" | cut -d'.' -f1)
    Limit=$(echo "$Limit" | cut -d'.' -f1)

    Available=$((Limit - CurrentValue))
    echo "✅ Model available - Model: $ModelType | Used: $CurrentValue | Limit: $Limit | Available: $Available"

    if (( Available < 1 )); then
        echo "❌ ERROR: Insufficient quota for model: $Model in location: $Location. Available: $Available, Requested: $IdealCapacity."
        exit 1
    elif (( Available < IdealCapacity )); then
        newCapacity=1
        if (( Available >= MinCapacity )); then
            newCapacity=$Available
        fi
        echo "🔧 Setting environment variable $CapacityEnvVarName to $newCapacity ..."
        azd env set "$CapacityEnvVarName" "$newCapacity"
        echo "❌ ERROR: Insufficient quota. Requested: $IdealCapacity. Downgraded to: $newCapacity."
    else
        echo "✅ Sufficient quota for model: $Model in location: $Location. Available: $Available, Requested: $IdealCapacity."
    fi
fi

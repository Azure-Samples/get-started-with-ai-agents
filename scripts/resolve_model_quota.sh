#!/bin/bash

# Initialize variables
Location=""
Model=""
Format=""
DeploymentType=""
CapacityEnvVarName=""
Capacity=""

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
        -Capacity)
            Capacity="$2"
            shift 2
            ;;
        -Format)
            Format="$2"
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
[[ -z "$Capacity" ]] && MissingParams+=("capacity")
[[ -z "$Format" ]] && MissingParams+=("format")
[[ -z "$DeploymentType" ]] && MissingParams+=("deployment-type")

if [[ ${#MissingParams[@]} -gt 0 ]]; then
    echo "❌ ERROR: Missing required parameters: ${MissingParams[*]}"
    echo "Usage: ./resolve_model_quota.sh -Location <Location> -Model <Model> -Format <Format> -Capacity <CAPACITY> -CapacityEnvVarName <ENV_VAR_NAME> [-DeploymentType <DeploymentType>]"
    exit 1
fi

if [[ "$DeploymentType" != "Standard" && "$DeploymentType" != "GlobalStandard" ]]; then
    echo "❌ ERROR: Invalid deployment type: $DeploymentType. Allowed values are 'Standard' or 'GlobalStandard'."
    exit 1
fi

ModelType="$Format.$DeploymentType.$Model"

echo "🔍 Checking quota for $ModelType in $Location ..."

ModelInfo=$(az cognitiveservices usage list --location "$Location" --query "[?name.value=='$ModelType']" --output json | tr '[:upper:]' '[:lower:]')

if [ -z "$ModelInfo" ]; then
    echo "❌ ERROR: No quota information found for model: $Model in location: $Location for model type: $ModelType."
    exit 1
fi

CurrentValue=$(echo "$ModelInfo" | awk -F': ' '/"currentvalue"/ {print $2}' | tr -d ',' | tr -d ' ')
Limit=$(echo "$ModelInfo" | awk -F': ' '/"limit"/ {print $2}' | tr -d ',' | tr -d ' ')

CurrentValue=${CurrentValue:-0}
Limit=${Limit:-0}

CurrentValue=$(echo "$CurrentValue" | cut -d'.' -f1)
Limit=$(echo "$Limit" | cut -d'.' -f1)

Available=$((Limit - CurrentValue))
echo "✅ Model available - Model: $ModelType | Used: $CurrentValue | Limit: $Limit | Available: $Available"

if [ "$Available" -lt "$Capacity" ]; then
    if [ "$Available" -ge 1 ]; then
        validInput=false
        while [ "$validInput" = false ]; do
            read -p "⚠️ ERROR: Insufficient quota. Available: $Available (in thousands of tokens per minute). Ideal was $Capacity. Please enter a new capacity (integer between 1 and $Available): " userInput

            if [[ "$userInput" =~ ^[0-9]+$ ]]; then
                if [ "$userInput" -ge 1 ] && [ "$userInput" -le "$Available" ]; then
                    newCapacity=$userInput
                    validInput=true
                else
                    echo "⚠️ WARNING: Invalid input. '$userInput' is not between 1 and $Available. Please try again." >&2
                fi
            else
                echo "⚠️ WARNING: Invalid input: '$userInput' is not a valid integer. Please try again." >&2
            fi
        done
        azd env set "$CapacityEnvVarName" "$newCapacity"
    else
        echo "❌ ERROR: Insufficient quota for model: $Model in location: $Location. Available: less than 1 (in thousands of tokens per minute), Requested: $Capacity." >&2
        exit 1
    fi
else
    echo "✅ Sufficient quota for model: $Model in location: $Location. Available: $Available, Requested: $Capacity."
fi

echo "Set exit code to 0"
exit 0

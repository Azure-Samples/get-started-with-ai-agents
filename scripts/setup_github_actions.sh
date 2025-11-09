#!/bin/bash

set -e

echo "🚀 GitHub Actions Setup for Azure Deployment"
echo "=============================================="
echo ""

# App Registration Details
APP_ID="db57485e-6284-434d-ba83-e8fb848cc01d"
TENANT_ID="b75007f5-364a-4c13-816e-74aacedc01a5"

# GitHub Repository Details
GITHUB_ORG="Skie-Art"
GITHUB_REPO="Ksenia-personal-agent"

echo "📋 Step 1: Creating Federated Credential for GitHub Actions"
echo "------------------------------------------------------------"

# Create federated credential for main branch
echo "Creating federated credential for branch: main"

CREDENTIAL_NAME="${GITHUB_REPO}-main"

az ad app federated-credential create \
  --id "$APP_ID" \
  --parameters "{
    \"name\": \"$CREDENTIAL_NAME\",
    \"issuer\": \"https://token.actions.githubusercontent.com\",
    \"subject\": \"repo:${GITHUB_ORG}/${GITHUB_REPO}:ref:refs/heads/main\",
    \"audiences\": [\"api://AzureADTokenExchange\"],
    \"description\": \"GitHub Actions deployment for main branch\"
  }" 2>/dev/null || echo "⚠️  Federated credential may already exist"

echo "✅ Federated credential configured"
echo ""

echo "📋 Step 2: Gathering Azure Resource Information"
echo "------------------------------------------------"

# Check if logged in
if ! az account show &>/dev/null; then
    echo "🔐 Not logged in to Azure. Please login..."
    az login --tenant "$TENANT_ID"
fi

# Get subscription ID
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
echo "Subscription ID: $SUBSCRIPTION_ID"

# Try to detect existing resources
echo ""
echo "🔍 Detecting existing Azure resources..."
echo ""

# Look for AI Foundry projects
echo "Looking for Azure AI Foundry projects..."
AI_PROJECTS=$(az resource list --resource-type "Microsoft.MachineLearningServices/workspaces" --query "[].{name:name, group:resourceGroup, location:location}" -o tsv 2>/dev/null || echo "")

if [ -n "$AI_PROJECTS" ]; then
    echo "Found AI Foundry projects:"
    echo "$AI_PROJECTS" | nl
    echo ""
    read -p "Enter the line number of your AI Project (or press Enter to enter manually): " PROJECT_CHOICE

    if [ -n "$PROJECT_CHOICE" ]; then
        PROJECT_INFO=$(echo "$AI_PROJECTS" | sed -n "${PROJECT_CHOICE}p")
        AIPROJECT_NAME=$(echo "$PROJECT_INFO" | awk '{print $1}')
        RESOURCE_GROUP=$(echo "$PROJECT_INFO" | awk '{print $2}')
        LOCATION=$(echo "$PROJECT_INFO" | awk '{print $3}')

        echo "Selected: $AIPROJECT_NAME in $RESOURCE_GROUP"

        # Get project endpoint
        PROJECT_ENDPOINT=$(az ml workspace show -n "$AIPROJECT_NAME" -g "$RESOURCE_GROUP" --query "discoveryUrl" -o tsv 2>/dev/null | sed 's/\/discovery$//' || echo "")

        # Get AI Project resource ID
        PROJECT_RESOURCE_ID=$(az resource show -g "$RESOURCE_GROUP" -n "$AIPROJECT_NAME" --resource-type "Microsoft.MachineLearningServices/workspaces" --query id -o tsv 2>/dev/null || echo "")
    fi
fi

# Manual entry if needed
if [ -z "$AIPROJECT_NAME" ]; then
    echo ""
    read -p "Enter your Azure AI Project name: " AIPROJECT_NAME
    read -p "Enter your Resource Group name: " RESOURCE_GROUP
    read -p "Enter your Azure location (e.g., eastus): " LOCATION
fi

# Get other resources in the resource group
echo ""
echo "🔍 Finding resources in resource group: $RESOURCE_GROUP"

# Container Registry
ACR_NAME=$(az acr list -g "$RESOURCE_GROUP" --query "[0].name" -o tsv 2>/dev/null || echo "")
echo "Container Registry: ${ACR_NAME:-Not found}"

# Storage Account
STORAGE_NAME=$(az storage account list -g "$RESOURCE_GROUP" --query "[0].name" -o tsv 2>/dev/null || echo "")
echo "Storage Account: ${STORAGE_NAME:-Not found}"

# Key Vault
KEYVAULT_NAME=$(az keyvault list -g "$RESOURCE_GROUP" --query "[0].name" -o tsv 2>/dev/null || echo "")
echo "Key Vault: ${KEYVAULT_NAME:-Not found}"

# AI Services
AI_SERVICES_NAME=$(az cognitiveservices account list -g "$RESOURCE_GROUP" --query "[0].name" -o tsv 2>/dev/null || echo "")
echo "AI Services: ${AI_SERVICES_NAME:-Not found}"

# AI Search (optional)
SEARCH_NAME=$(az search service list -g "$RESOURCE_GROUP" --query "[0].name" -o tsv 2>/dev/null || echo "")
echo "AI Search: ${SEARCH_NAME:-Not found (optional)}"

# Application Insights (optional)
APP_INSIGHTS_NAME=$(az monitor app-insights component list -g "$RESOURCE_GROUP" --query "[0].name" -o tsv 2>/dev/null || echo "")
echo "Application Insights: ${APP_INSIGHTS_NAME:-Not found (optional)}"

# Log Analytics Workspace (optional)
LOG_ANALYTICS_NAME=$(az monitor log-analytics workspace list -g "$RESOURCE_GROUP" --query "[0].name" -o tsv 2>/dev/null || echo "")
echo "Log Analytics: ${LOG_ANALYTICS_NAME:-Not found (optional)}"

echo ""
echo "📋 Step 3: Agent Information"
echo "----------------------------"
read -p "Enter your Agent ID from Azure AI Foundry: " AGENT_ID
read -p "Enter your Agent Name (default: agent-template-assistant): " AGENT_NAME
AGENT_NAME=${AGENT_NAME:-agent-template-assistant}

echo ""
echo "📋 Step 4: Configuration"
echo "------------------------"
read -p "Are you using AI Search? (yes/no, default: no): " USE_SEARCH
USE_SEARCH=${USE_SEARCH:-no}
USE_AI_SEARCH=$([ "$USE_SEARCH" = "yes" ] && echo "true" || echo "false")

read -p "Are you using Application Insights? (yes/no, default: yes): " USE_INSIGHTS
USE_INSIGHTS=${USE_INSIGHTS:-yes}
USE_APP_INSIGHTS=$([ "$USE_INSIGHTS" = "yes" ] && echo "true" || echo "false")

echo ""
echo "✅ Configuration complete!"
echo ""
echo "=========================================="
echo "📝 GitHub Repository Variables to Set"
echo "=========================================="
echo ""
echo "Go to: https://github.com/$GITHUB_ORG/$GITHUB_REPO/settings/variables/actions"
echo ""
echo "Click 'New repository variable' and add each of these:"
echo ""

cat << EOF
# Authentication
AZURE_CLIENT_ID = $APP_ID
AZURE_TENANT_ID = $TENANT_ID
AZURE_SUBSCRIPTION_ID = $SUBSCRIPTION_ID

# Environment
AZURE_ENV_NAME = prod
AZURE_LOCATION = $LOCATION
AZURE_RESOURCE_GROUP = $RESOURCE_GROUP

# AI Resources
AZURE_AIPROJECT_NAME = $AIPROJECT_NAME
${AIHUB_NAME:+AZURE_AIHUB_NAME = $AIHUB_NAME}
${AI_SERVICES_NAME:+AZURE_AISERVICES_NAME = $AI_SERVICES_NAME}

# Infrastructure
${ACR_NAME:+AZURE_CONTAINER_REGISTRY_NAME = $ACR_NAME}
${KEYVAULT_NAME:+AZURE_KEYVAULT_NAME = $KEYVAULT_NAME}
${STORAGE_NAME:+AZURE_STORAGE_ACCOUNT_NAME = $STORAGE_NAME}
${SEARCH_NAME:+AZURE_SEARCH_SERVICE_NAME = $SEARCH_NAME}
${APP_INSIGHTS_NAME:+AZURE_APPLICATION_INSIGHTS_NAME = $APP_INSIGHTS_NAME}
${LOG_ANALYTICS_NAME:+AZURE_LOG_ANALYTICS_WORKSPACE_NAME = $LOG_ANALYTICS_NAME}

# Configuration Flags
USE_CONTAINER_REGISTRY = true
USE_APPLICATION_INSIGHTS = $USE_APP_INSIGHTS
USE_AZURE_AI_SEARCH_SERVICE = $USE_AI_SEARCH

# Agent Configuration
AZURE_AI_AGENT_NAME = $AGENT_NAME
AZURE_EXISTING_AGENT_ID = $AGENT_ID
AZURE_AI_AGENT_DEPLOYMENT_NAME = gpt-5-mini
AZURE_AI_AGENT_MODEL_NAME = gpt-5-mini
AZURE_AI_AGENT_MODEL_FORMAT = OpenAI
AZURE_AI_AGENT_MODEL_VERSION = 2024-07-18
AZURE_AI_AGENT_DEPLOYMENT_SKU = GlobalStandard
AZURE_AI_AGENT_DEPLOYMENT_CAPACITY = 80

# Embedding Model (if using AI Search)
AZURE_AI_EMBED_DEPLOYMENT_NAME = text-embedding-3-small
AZURE_AI_EMBED_MODEL_NAME = text-embedding-3-small
AZURE_AI_EMBED_MODEL_FORMAT = OpenAI
AZURE_AI_EMBED_MODEL_VERSION = 1
AZURE_AI_EMBED_DEPLOYMENT_SKU = Standard
AZURE_AI_EMBED_DEPLOYMENT_CAPACITY = 50

# Existing Project
${PROJECT_RESOURCE_ID:+AZURE_EXISTING_AIPROJECT_RESOURCE_ID = $PROJECT_RESOURCE_ID}
${PROJECT_ENDPOINT:+AZURE_EXISTING_AIPROJECT_ENDPOINT = $PROJECT_ENDPOINT}
EOF

echo ""
echo "=========================================="
echo "📄 Save this to a file for reference"
echo "=========================================="
echo ""

# Save to file
OUTPUT_FILE="github_actions_variables.txt"
cat > "$OUTPUT_FILE" << EOF
GitHub Actions Variables for $GITHUB_ORG/$GITHUB_REPO
Generated: $(date)

# Authentication
AZURE_CLIENT_ID = $APP_ID
AZURE_TENANT_ID = $TENANT_ID
AZURE_SUBSCRIPTION_ID = $SUBSCRIPTION_ID

# Environment
AZURE_ENV_NAME = prod
AZURE_LOCATION = $LOCATION
AZURE_RESOURCE_GROUP = $RESOURCE_GROUP

# AI Resources
AZURE_AIPROJECT_NAME = $AIPROJECT_NAME
${AIHUB_NAME:+AZURE_AIHUB_NAME = $AIHUB_NAME}
${AI_SERVICES_NAME:+AZURE_AISERVICES_NAME = $AI_SERVICES_NAME}

# Infrastructure
${ACR_NAME:+AZURE_CONTAINER_REGISTRY_NAME = $ACR_NAME}
${KEYVAULT_NAME:+AZURE_KEYVAULT_NAME = $KEYVAULT_NAME}
${STORAGE_NAME:+AZURE_STORAGE_ACCOUNT_NAME = $STORAGE_NAME}
${SEARCH_NAME:+AZURE_SEARCH_SERVICE_NAME = $SEARCH_NAME}
${APP_INSIGHTS_NAME:+AZURE_APPLICATION_INSIGHTS_NAME = $APP_INSIGHTS_NAME}
${LOG_ANALYTICS_NAME:+AZURE_LOG_ANALYTICS_WORKSPACE_NAME = $LOG_ANALYTICS_NAME}

# Configuration Flags
USE_CONTAINER_REGISTRY = true
USE_APPLICATION_INSIGHTS = $USE_APP_INSIGHTS
USE_AZURE_AI_SEARCH_SERVICE = $USE_AI_SEARCH

# Agent Configuration
AZURE_AI_AGENT_NAME = $AGENT_NAME
AZURE_EXISTING_AGENT_ID = $AGENT_ID
AZURE_AI_AGENT_DEPLOYMENT_NAME = gpt-5-mini
AZURE_AI_AGENT_MODEL_NAME = gpt-5-mini
AZURE_AI_AGENT_MODEL_FORMAT = OpenAI
AZURE_AI_AGENT_MODEL_VERSION = 2024-07-18
AZURE_AI_AGENT_DEPLOYMENT_SKU = GlobalStandard
AZURE_AI_AGENT_DEPLOYMENT_CAPACITY = 80

# Embedding Model
AZURE_AI_EMBED_DEPLOYMENT_NAME = text-embedding-3-small
AZURE_AI_EMBED_MODEL_NAME = text-embedding-3-small
AZURE_AI_EMBED_MODEL_FORMAT = OpenAI
AZURE_AI_EMBED_MODEL_VERSION = 1
AZURE_AI_EMBED_DEPLOYMENT_SKU = Standard
AZURE_AI_EMBED_DEPLOYMENT_CAPACITY = 50

# Existing Project
${PROJECT_RESOURCE_ID:+AZURE_EXISTING_AIPROJECT_RESOURCE_ID = $PROJECT_RESOURCE_ID}
${PROJECT_ENDPOINT:+AZURE_EXISTING_AIPROJECT_ENDPOINT = $PROJECT_ENDPOINT}
EOF

echo "✅ Configuration saved to: $OUTPUT_FILE"
echo ""
echo "=========================================="
echo "🎯 Next Steps"
echo "=========================================="
echo ""
echo "1. Go to GitHub: https://github.com/$GITHUB_ORG/$GITHUB_REPO/settings/variables/actions"
echo "2. Add all the variables listed above"
echo "3. Enable GitHub Actions: https://github.com/$GITHUB_ORG/$GITHUB_REPO/actions"
echo "4. Test deployment: Go to Actions → 'Deploy to Azure' → 'Run workflow'"
echo ""
echo "✨ Setup complete!"

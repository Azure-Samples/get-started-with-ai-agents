#!/bin/bash

set -e

echo "🚀 Setting GitHub Actions Variables"
echo "===================================="
echo ""

# GitHub repository
REPO="Skie-Art/Ksenia-personal-agent"

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) is not installed."
    echo ""
    echo "Install it from: https://cli.github.com/"
    echo ""
    echo "Or install via:"
    echo "  - macOS: brew install gh"
    echo "  - Windows: winget install GitHub.cli"
    echo "  - Linux: See https://github.com/cli/cli/blob/trunk/docs/install_linux.md"
    echo ""
    exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo "🔐 Not authenticated with GitHub. Logging in..."
    gh auth login
fi

echo "Setting variables for repository: $REPO"
echo ""

# Core Authentication & Environment
gh variable set AZURE_CLIENT_ID -b "db57485e-6284-434d-ba83-e8fb848cc01d" -R "$REPO"
gh variable set AZURE_TENANT_ID -b "b75007f5-364a-4c13-816e-74aacedc01a5" -R "$REPO"
gh variable set AZURE_SUBSCRIPTION_ID -b "95a864d4-ff8f-4cfa-ae93-f3b9a1ba5ae6" -R "$REPO"
gh variable set AZURE_ENV_NAME -b "prod" -R "$REPO"
gh variable set AZURE_LOCATION -b "eastus" -R "$REPO"
gh variable set AZURE_RESOURCE_GROUP -b "rg-Ksenia-personal-agent" -R "$REPO"

echo "✅ Authentication & Environment variables set"

# AI Resources
gh variable set AZURE_AIPROJECT_NAME -b "proj-fpfde4hlibpgs" -R "$REPO"
gh variable set AZURE_AISERVICES_NAME -b "aoai-fpfde4hlibpgs" -R "$REPO"
gh variable set AZURE_AIHUB_NAME -b "aoai-fpfde4hlibpgs" -R "$REPO"

echo "✅ AI Resources variables set"

# Infrastructure
gh variable set AZURE_CONTAINER_REGISTRY_NAME -b "crfpfde4hlibpgs" -R "$REPO"
gh variable set AZURE_STORAGE_ACCOUNT_NAME -b "stfpfde4hlibpgs" -R "$REPO"

echo "✅ Infrastructure variables set"

# Configuration Flags
gh variable set USE_CONTAINER_REGISTRY -b "true" -R "$REPO"
gh variable set USE_APPLICATION_INSIGHTS -b "false" -R "$REPO"
gh variable set USE_AZURE_AI_SEARCH_SERVICE -b "false" -R "$REPO"

echo "✅ Configuration flags set"

# Agent Configuration
gh variable set AZURE_AI_AGENT_NAME -b "agent-template-assistant" -R "$REPO"
gh variable set AZURE_EXISTING_AGENT_ID -b "asst_LwEiFvlTxOwrDx50QMTaJn2w" -R "$REPO"
gh variable set AZURE_AI_AGENT_DEPLOYMENT_NAME -b "gpt-5-mini" -R "$REPO"
gh variable set AZURE_AI_AGENT_MODEL_NAME -b "gpt-5-mini" -R "$REPO"
gh variable set AZURE_AI_AGENT_MODEL_FORMAT -b "OpenAI" -R "$REPO"
gh variable set AZURE_AI_AGENT_MODEL_VERSION -b "2024-07-18" -R "$REPO"
gh variable set AZURE_AI_AGENT_DEPLOYMENT_SKU -b "GlobalStandard" -R "$REPO"
gh variable set AZURE_AI_AGENT_DEPLOYMENT_CAPACITY -b "80" -R "$REPO"

echo "✅ Agent configuration set (using gpt-5-mini)"

# Embedding Model
gh variable set AZURE_AI_EMBED_DEPLOYMENT_NAME -b "text-embedding-3-small" -R "$REPO"
gh variable set AZURE_AI_EMBED_MODEL_NAME -b "text-embedding-3-small" -R "$REPO"
gh variable set AZURE_AI_EMBED_MODEL_FORMAT -b "OpenAI" -R "$REPO"
gh variable set AZURE_AI_EMBED_MODEL_VERSION -b "1" -R "$REPO"
gh variable set AZURE_AI_EMBED_DEPLOYMENT_SKU -b "Standard" -R "$REPO"
gh variable set AZURE_AI_EMBED_DEPLOYMENT_CAPACITY -b "50" -R "$REPO"

echo "✅ Embedding model configuration set"

# Existing Project
gh variable set AZURE_EXISTING_AIPROJECT_RESOURCE_ID -b "/subscriptions/95a864d4-ff8f-4cfa-ae93-f3b9a1ba5ae6/resourceGroups/rg-Ksenia-personal-agent/providers/Microsoft.CognitiveServices/accounts/aoai-fpfde4hlibpgs/projects/proj-fpfde4hlibpgs" -R "$REPO"
gh variable set AZURE_EXISTING_AIPROJECT_ENDPOINT -b "https://aoai-fpfde4hlibpgs.services.ai.azure.com/api/projects/proj-fpfde4hlibpgs" -R "$REPO"

echo "✅ Existing project configuration set"

echo ""
echo "=========================================="
echo "✅ All GitHub Actions variables configured!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Enable GitHub Actions: https://github.com/$REPO/actions"
echo "2. Run a deployment: Actions → 'Deploy to Azure' → 'Run workflow'"
echo ""
echo "View all variables: https://github.com/$REPO/settings/variables/actions"

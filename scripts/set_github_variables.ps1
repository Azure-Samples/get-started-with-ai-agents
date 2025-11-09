# PowerShell script to set GitHub Actions variables

$ErrorActionPreference = "Stop"

Write-Host "🚀 Setting GitHub Actions Variables" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# GitHub repository
$REPO = "Skie-Art/Ksenia-personal-agent"

# Check if gh CLI is installed
try {
    gh --version | Out-Null
} catch {
    Write-Host "❌ GitHub CLI (gh) is not installed." -ForegroundColor Red
    Write-Host ""
    Write-Host "Install it from: https://cli.github.com/" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Or install via:" -ForegroundColor Yellow
    Write-Host "  - Windows: winget install GitHub.cli" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

# Check if authenticated
try {
    gh auth status | Out-Null
} catch {
    Write-Host "🔐 Not authenticated with GitHub. Logging in..." -ForegroundColor Yellow
    gh auth login
}

Write-Host "Setting variables for repository: $REPO" -ForegroundColor Green
Write-Host ""

# Core Authentication & Environment
gh variable set AZURE_CLIENT_ID -b "db57485e-6284-434d-ba83-e8fb848cc01d" -R $REPO
gh variable set AZURE_TENANT_ID -b "b75007f5-364a-4c13-816e-74aacedc01a5" -R $REPO
gh variable set AZURE_SUBSCRIPTION_ID -b "95a864d4-ff8f-4cfa-ae93-f3b9a1ba5ae6" -R $REPO
gh variable set AZURE_ENV_NAME -b "prod" -R $REPO
gh variable set AZURE_LOCATION -b "eastus" -R $REPO
gh variable set AZURE_RESOURCE_GROUP -b "rg-Ksenia-personal-agent" -R $REPO

Write-Host "✅ Authentication & Environment variables set" -ForegroundColor Green

# AI Resources
gh variable set AZURE_AIPROJECT_NAME -b "proj-fpfde4hlibpgs" -R $REPO
gh variable set AZURE_AISERVICES_NAME -b "aoai-fpfde4hlibpgs" -R $REPO
gh variable set AZURE_AIHUB_NAME -b "aoai-fpfde4hlibpgs" -R $REPO

Write-Host "✅ AI Resources variables set" -ForegroundColor Green

# Infrastructure
gh variable set AZURE_CONTAINER_REGISTRY_NAME -b "crfpfde4hlibpgs" -R $REPO
gh variable set AZURE_STORAGE_ACCOUNT_NAME -b "stfpfde4hlibpgs" -R $REPO

Write-Host "✅ Infrastructure variables set" -ForegroundColor Green

# Configuration Flags
gh variable set USE_CONTAINER_REGISTRY -b "true" -R $REPO
gh variable set USE_APPLICATION_INSIGHTS -b "false" -R $REPO
gh variable set USE_AZURE_AI_SEARCH_SERVICE -b "false" -R $REPO

Write-Host "✅ Configuration flags set" -ForegroundColor Green

# Agent Configuration
gh variable set AZURE_AI_AGENT_NAME -b "agent-template-assistant" -R $REPO
gh variable set AZURE_EXISTING_AGENT_ID -b "asst_LwEiFvlTxOwrDx50QMTaJn2w" -R $REPO
gh variable set AZURE_AI_AGENT_DEPLOYMENT_NAME -b "gpt-5-mini" -R $REPO
gh variable set AZURE_AI_AGENT_MODEL_NAME -b "gpt-5-mini" -R $REPO
gh variable set AZURE_AI_AGENT_MODEL_FORMAT -b "OpenAI" -R $REPO
gh variable set AZURE_AI_AGENT_MODEL_VERSION -b "2024-07-18" -R $REPO
gh variable set AZURE_AI_AGENT_DEPLOYMENT_SKU -b "GlobalStandard" -R $REPO
gh variable set AZURE_AI_AGENT_DEPLOYMENT_CAPACITY -b "80" -R $REPO

Write-Host "✅ Agent configuration set (using gpt-5-mini)" -ForegroundColor Green

# Embedding Model
gh variable set AZURE_AI_EMBED_DEPLOYMENT_NAME -b "text-embedding-3-small" -R $REPO
gh variable set AZURE_AI_EMBED_MODEL_NAME -b "text-embedding-3-small" -R $REPO
gh variable set AZURE_AI_EMBED_MODEL_FORMAT -b "OpenAI" -R $REPO
gh variable set AZURE_AI_EMBED_MODEL_VERSION -b "1" -R $REPO
gh variable set AZURE_AI_EMBED_DEPLOYMENT_SKU -b "Standard" -R $REPO
gh variable set AZURE_AI_EMBED_DEPLOYMENT_CAPACITY -b "50" -R $REPO

Write-Host "✅ Embedding model configuration set" -ForegroundColor Green

# Existing Project
gh variable set AZURE_EXISTING_AIPROJECT_RESOURCE_ID -b "/subscriptions/95a864d4-ff8f-4cfa-ae93-f3b9a1ba5ae6/resourceGroups/rg-Ksenia-personal-agent/providers/Microsoft.CognitiveServices/accounts/aoai-fpfde4hlibpgs/projects/proj-fpfde4hlibpgs" -R $REPO
gh variable set AZURE_EXISTING_AIPROJECT_ENDPOINT -b "https://aoai-fpfde4hlibpgs.services.ai.azure.com/api/projects/proj-fpfde4hlibpgs" -R $REPO

Write-Host "✅ Existing project configuration set" -ForegroundColor Green

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "✅ All GitHub Actions variables configured!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Enable GitHub Actions: https://github.com/$REPO/actions" -ForegroundColor Yellow
Write-Host "2. Run a deployment: Actions → 'Deploy to Azure' → 'Run workflow'" -ForegroundColor Yellow
Write-Host ""
Write-Host "View all variables: https://github.com/$REPO/settings/variables/actions" -ForegroundColor Cyan

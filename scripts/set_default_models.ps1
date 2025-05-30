param (
    [string]$SubscriptionId,
    [string]$Location
)
# Verify all required parameters are provided
$MissingParams = @()

if (-not $SubscriptionId) {
    $MissingParams += "subscription"
}

if (-not $Location) {
    $MissingParams += "location"
}


if ($MissingParams.Count -gt 0) {
    Write-Error "❌ ERROR: Missing required parameters: $($MissingParams -join ', ')"
    Write-Host "Usage: .\set_default_models.ps1 -SubscriptionId <SUBSCRIPTION_ID> -Location <LOCATION> -ModelsParameter <MODELS_PARAMETER>"
    exit 1
}


$defaultEnvVars = @{
    AZURE_AI_EMBED_DEPLOYMENT_NAME = 'text-embedding-3-small'
    AZURE_AI_EMBED_MODEL_NAME = 'text-embedding-3-small'
    AZURE_AI_EMBED_MODEL_FORMAT = 'OpenAI'
    AZURE_AI_EMBED_MODEL_VERSION = '1'
    AZURE_AI_EMBED_DEPLOYMENT_SKU = 'Standard'
    AZURE_AI_EMBED_DEPLOYMENT_CAPACITY = '50'
    AZURE_AI_AGENT_DEPLOYMENT_NAME = 'gpt-4o-mini'
    AZURE_AI_AGENT_MODEL_NAME = 'gpt-4o-mini'
    AZURE_AI_AGENT_MODEL_VERSION = '2024-07-18'
    AZURE_AI_AGENT_MODEL_FORMAT = 'OpenAI'
    AZURE_AI_AGENT_DEPLOYMENT_SKU = 'GlobalStandard'
    AZURE_AI_AGENT_DEPLOYMENT_CAPACITY = '80'
}

$envVars = @{}

foreach ($key in $defaultEnvVars.Keys) {
    $val = [System.Environment]::GetEnvironmentVariable($key, "Process")
    $envVars[$key] = $val
    if (-not $val) {
        $envVars[$key] = $defaultEnvVars[$key]
    }
    azd env set $key $envVars[$key]
}

$chatDeployment = @{
    name = $envVars.AZURE_AI_AGENT_DEPLOYMENT_NAME
    model = @{
        name = $envVars.AZURE_AI_AGENT_MODEL_NAME
        version = $envVars.AZURE_AI_AGENT_MODEL_VERSION
        format = $envVars.AZURE_AI_AGENT_MODEL_FORMAT
    }
    sku = @{
        name = $envVars.AZURE_AI_AGENT_DEPLOYMENT_SKU
        ideal_capacity = $envVars.AZURE_AI_AGENT_DEPLOYMENT_CAPACITY
        min_capacity = 30
    } 
    capacity_env_var_name = 'AZURE_AI_AGENT_DEPLOYMENT_CAPACITY'
}



$aiModelDeployments = @($chatDeployment)

$useSearchService = ([System.Environment]::GetEnvironmentVariable('USE_AZURE_AI_SEARCH_SERVICE', "Process"))

if ($useSearchService -eq 'true') {
    $embedDeployment = @{
        name = $envVars.AZURE_AI_EMBED_DEPLOYMENT_NAME
        model = @{
            name = $envVars.AZURE_AI_EMBED_MODEL_NAME
            version = $envVars.AZURE_AI_EMBED_MODEL_VERSION
            format = $envVars.AZURE_AI_EMBED_MODEL_FORMAT
        }
        sku = @{
            name = $envVars.AZURE_AI_EMBED_DEPLOYMENT_SKU
            ideal_capacity = $envVars.AZURE_AI_EMBED_DEPLOYMENT_CAPACITY
            min_capacity = 30
        }
        capacity_env_var_name = 'AZURE_AI_EMBED_DEPLOYMENT_CAPACITY'
    }

    $aiModelDeployments += $embedDeployment
}


az account set --subscription $SubscriptionId
Write-Host "🎯 Active Subscription: $(az account show --query '[name, id]' --output tsv)"

$QuotaAvailable = $true

foreach ($deployment in $aiModelDeployments) {
    $name = $deployment.name
    $model = $deployment.model.name
    $type = $deployment.sku.name
    $ideal_capacity = $deployment.sku.ideal_capacity
    $min_capacity = $deployment.sku.min_capacity
    $capacity_env_var_name = $deployment.capacity_env_var_name
    Write-Host "🔍 Validating model deployment: $name ..."
    & .\scripts\resolve_model_quota.ps1 -Location $Location -Model $model -IdealCapacity $ideal_capacity -MinCapacity $min_capacity -CapacityEnvVarName $capacity_env_var_name -DeploymentType $type

    # Check if the script failed
    if ($LASTEXITCODE -ne 0) {
        Write-Error "❌ ERROR: Quota validation failed for model deployment: $name"
        $QuotaAvailable = $false
    }
}


if (-not $QuotaAvailable) {
    exit 1
} else {
    Write-Host "✅ All model deployments passed quota validation successfully."
    exit 0
}
param (
    [string]$Location,
    [string]$Model,
    [string]$Format,
    [string]$DeploymentType,
    [string]$CapacityEnvVarName,
    [int]$Capacity
)

# Verify all required parameters are provided
$MissingParams = @()

if (-not $Location) {
    $MissingParams += "location"
}

if (-not $Model) {
    $MissingParams += "model"
}

if (-not $Capacity) {
    $MissingParams += "capacity"
}

if (-not $Format) {
    $MissingParams += "format"
}

if (-not $DeploymentType) {
    $MissingParams += "deployment-type"
}

if ($MissingParams.Count -gt 0) {
    Write-Error "❌ ERROR: Missing required parameters: $($MissingParams -join ', ')"
    Write-Host "Usage: .\resolve_model_quota.ps1 -Location <LOCATION> -Model <MODEL> -Format <FORMAT> -Capacity <CAPACITY> -CapacityEnvVarName <ENV_VAR_NAME> [-DeploymentType <DEPLOYMENT_TYPE>]"
    exit 1
}

if ($DeploymentType -ne "Standard" -and $DeploymentType -ne "GlobalStandard") {
    Write-Error "❌ ERROR: Invalid deployment type: $DeploymentType. Allowed values are 'Standard' or 'GlobalStandard'."
    exit 1
}

$ModelType = "$Format.$DeploymentType.$Model"

Write-Host "🔍 Checking quota for $ModelType in $Location ..."

# Get model quota information
$ModelInfo = az cognitiveservices usage list --location $Location --query "[?name.value=='$ModelType'] | [0]" --output json | ConvertFrom-Json
if (-not $ModelInfo) {
    Write-Error "❌ ERROR: No quota information found for model: $Model in location: $Location for model type: $ModelType."
    exit 1
}


$CurrentValue =$ModelInfo.currentValue
$Limit = $ModelInfo.limit

$CurrentValue = [int]($CurrentValue -replace '\.0+$', '') # Remove decimals
$Limit = [int]($Limit -replace '\.0+$', '') # Remove decimals

$Available = $Limit - $CurrentValue
Write-Host "✅ Model available - Model: $ModelType | Used: $CurrentValue | Limit: $Limit | Available: $Available"


if ($Available -lt $Capacity) {

    # Determine newCapacity based on user prompt or availability
    # This logic assumes it will replace the subsequent lines that also set $newCapacity.
    if ($Available -ge 1) {
        $validInput = $false
        # $newCapacity will be set by user input if $Available >= 1
        do {
        $userInput = Read-Host "⚠️ ERROR: Insufficient quota. Available: $Available (in thousands of tokens per minute). Ideal is $Capacity. Please enter a new capacity (integer between 1 and $Available): "
        
        $parsedInt = 0 # Variable to hold the parsed integer
        if ([int]::TryParse($userInput, [ref]$parsedInt)) {
            if ($parsedInt -ge 1 -and $parsedInt -le $Available) {
            $newCapacity = $parsedInt # Set $newCapacity to the user's valid choice
            $validInput = $true
            } else {
            Write-Warning "Invalid input. '$parsedInt' is not between 1 and $Available. Please try again."
            }
        } else {
            Write-Warning "Invalid input: '$userInput' is not a valid integer. Please try again."
        }
        } while (-not $validInput)
        azd env set $CapacityEnvVarName $newCapacity
    } else { 
        # This case handles when $Available is 0 or less (though quota is typically non-negative).
        # Prompting for "between 1 and $Available" is not possible.
        Write-Error "❌ ERROR: Insufficient quota for model: $Model in location: $Location. Available: less than 1 (in thousands of tokens per minute), Requested: $Capacity."
        exit 1
    }
    
} else {
    Write-Host "✅ Sufficient quota for model: $Model in location: $Location. Available: $Available, Requested: $Capacity."
}

exit 0

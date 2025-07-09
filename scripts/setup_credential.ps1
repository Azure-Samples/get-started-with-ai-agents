# Check Azure login status
$azAccount = az account show 2>$null

if (-not $azAccount) {
    
    Write-Host "🔐 Not logged in to Azure. Attempting to login..." -ForegroundColor Yellow
    $azureTenantId = azd env get-value AZURE_TENANT_ID
    az login --tenant $azureTenantId | Out-Null

    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Azure login failed. Exiting script." -ForegroundColor Red
        exit 1
    }

    Write-Host "✅ Logged in to Azure successfully." -ForegroundColor Green
} else {
    $accountInfo = $azAccount | ConvertFrom-Json
    Write-Host "✅ Already logged in as: $($accountInfo.user.name)" -ForegroundColor Green
}

# Prompt for username with validation
do {
    $username = Read-Host -Prompt '👤 Create a new username for the web app (no spaces, at least 1 character)'
    $usernameInvalid = $false
    if ([string]::IsNullOrWhiteSpace($username)) {
        Write-Warning "❌ Username cannot be empty or consist only of whitespace."
        $usernameInvalid = $true
    } elseif ($username -match '\s') {
        Write-Warning "❌ Username cannot contain spaces."
        $usernameInvalid = $true
    }
} while ($usernameInvalid)

# Prompt for password with validation
do {
    $password = Read-Host -Prompt '🔑 Create a new password for the web app (no spaces, at least 1 character)' -AsSecureString
    $confirmPassword = Read-Host -Prompt '🔑 Confirm the new password' -AsSecureString
    $passwordInvalid = $false

    if ($password.Length -eq 0) {
        Write-Warning "❌ Password cannot be empty."
        $passwordInvalid = $true
    } elseif ($password.Length -ne $confirmPassword.Length) { # Quick check for length difference
        Write-Warning "❌ Passwords do not match."
        $passwordInvalid = $true
    } else {
        # Convert SecureStrings to plain text for validation and comparison
        $tempBSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($password)
        $tempPlainPassword = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($tempBSTR)

        $confirmBSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($confirmPassword)
        $confirmPlainPassword = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($confirmBSTR)

        if ($tempPlainPassword -ne $confirmPlainPassword) {
            Write-Warning "❌ Passwords do not match."
            $passwordInvalid = $true
        } elseif ($tempPlainPassword -match '\s') {
            Write-Warning "❌ Password cannot contain spaces."
            $passwordInvalid = $true
        }
        
        # Securely clear the plain text passwords from memory after validation
        [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($tempBSTR)
        [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($confirmBSTR)
        Remove-Variable tempBSTR, tempPlainPassword, confirmBSTR, confirmPlainPassword -ErrorAction SilentlyContinue
    }
} while ($passwordInvalid)


# Convert the secure string password to plain text
$BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($password)
$plainPassword = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)

$resourceGroupName = azd env get-value AZURE_RESOURCE_GROUP
$containerAppName = azd env get-value SERVICE_API_NAME
$subscriptionId = azd env get-value AZURE_SUBSCRIPTION_ID

az account set --subscription $subscriptionId
Write-Host "🎯 Active Subscription: $(az account show --query '[name, id]' --output tsv)"


Write-Host "⏳ Setup username and password in the secrets..."

# Set the secret
az containerapp secret set `
  --name $containerAppName `
  --resource-group $resourceGroupName `
  --secrets web-app-username=$username web-app-password=$plainPassword `
  > $null 2>&1

#set the environment variables to reference the secrets
az containerapp update `
  --name $containerAppName `
  --resource-group $resourceGroupName `
  --set-env-vars WEB_APP_USERNAME=secretref:web-app-username WEB_APP_PASSWORD=secretref:web-app-password `
  > $null 2>&1


Write-Host "✅ New username and password now are in the secrets"
Write-Host "🔍 Querying the active revision in the container app..."

# Get the active revision name
$activeRevision = az containerapp revision list `
    --name $containerAppName `
    --resource-group $resourceGroupName `
    --query '[?properties.active==`true`].name' `
    --output tsv

if (-not $activeRevision) {
    Write-Host "❌ No active revision found for the specified Container App."
    exit 1
}

Write-Host "♻️ Restarting revision $activeRevision...."


# Restart the active revision
az containerapp revision restart `
    --name $containerAppName `
    --resource-group $resourceGroupName `
    --revision $activeRevision `
    > $null 2>&1

Write-Host "✅ Successfully restarted the revision: $activeRevision"

exit 0
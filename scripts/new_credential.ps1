# Prompt for username and password
# Prompt for username with validation
do {
    $username = Read-Host -Prompt 'Create a new username for the web app (no spaces, at least 1 character)'
    $usernameInvalid = $false
    if ([string]::IsNullOrWhiteSpace($username)) {
        Write-Warning "Username cannot be empty or consist only of whitespace."
        $usernameInvalid = $true
    } elseif ($username -match '\s') {
        Write-Warning "Username cannot contain spaces."
        $usernameInvalid = $true
    }
} while ($usernameInvalid)

# Prompt for password with validation
do {
    $password = Read-Host -Prompt 'Create a new password for the web app (no spaces, at least 1 character)' -AsSecureString
    $passwordInvalid = $false
    if ($password.Length -eq 0) {
        Write-Warning "Password cannot be empty."
        $passwordInvalid = $true
    } else {
        # Convert SecureString to plain text for space validation
        $tempBSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($password)
        $tempPlainPassword = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($tempBSTR)
        
        # Securely clear the plain text password from memory after validation
        [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($tempBSTR)
        Remove-Variable tempBSTR -ErrorAction SilentlyContinue
        Remove-Variable tempPlainPassword -ErrorAction SilentlyContinue # Ensure plain text is cleared

        if ($tempPlainPassword -match '\s') {
            Write-Warning "Password cannot contain spaces."
            $passwordInvalid = $true
        }
    }
} while ($passwordInvalid)

# Convert the secure string password to plain text
$BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($password)
$plainPassword = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)

# Set the environment variables using azd
azd env set WEB_APP_USERNAME $username
azd env set WEB_APP_PASSWORD $plainPassword

Write-Host "Username and password have been saved to AZD environment variables."

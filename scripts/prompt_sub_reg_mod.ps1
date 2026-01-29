<#
	Prompts to select an Azure subscription and region, then writes them
	to the active azd environment as AZURE_SUBSCRIPTION_ID and AZURE_LOCATION.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Ensure-Command {
	param(
		[Parameter(Mandatory)] [string] $Name
	)
	if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
		throw "Required command '$Name' not found. Install it and retry."
	}
}

Ensure-Command -Name az
Ensure-Command -Name azd

# Check if subscription and region are already set
$existingSubId = $null
$existingLocation = $null
try {
	$envVars = azd env get-values 2>$null
	if ($envVars) {
		$subLine = $envVars | Where-Object { $_ -match '^AZURE_SUBSCRIPTION_ID=' }
		if ($subLine) {
			$existingSubId = ($subLine -replace 'AZURE_SUBSCRIPTION_ID="(.+)"', '$1').Trim('"')
		}
		$locLine = $envVars | Where-Object { $_ -match '^AZURE_LOCATION=' }
		if ($locLine) {
			$existingLocation = ($locLine -replace 'AZURE_LOCATION="(.+)"', '$1').Trim('"')
		}
	}
} catch {
	$existingSubId = $null
	$existingLocation = $null
}

if (-not [string]::IsNullOrWhiteSpace($existingSubId) -and -not [string]::IsNullOrWhiteSpace($existingLocation)) {
	Write-Host "Subscription and region already configured in azd environment:" -ForegroundColor Green
	Write-Host "  Subscription ID: $existingSubId"
	Write-Host "  Location: $existingLocation"
	Write-Host "No changes needed. Exiting." -ForegroundColor Green
	exit 0
} else {
	# Ensure the user is logged in; only call az login if required
	try {
		az account show 1>$null 2>$null
	} catch {
		Write-Host 'Not logged in. Launching az login...' -ForegroundColor Yellow
		az login | Out-Null
	}

	Write-Host "Fetching subscriptions..."
	$subscriptions = az account list | ConvertFrom-Json | Sort-Object name
	if (-not $subscriptions -or $subscriptions.Count -eq 0) {
		throw 'No subscriptions found for the signed-in account.'
	}

	Write-Host 'Subscriptions:'
	for ($i = 0; $i -lt $subscriptions.Count; $i++) {
		$sub = $subscriptions[$i]
		Write-Host ("{0,2}. {1} ({2})" -f $i, $sub.name, $sub.id)
	}


	# Combined filter/selection loop for subscriptions (single prompt)
	$subIndex = $null
	$currentSubs = $subscriptions
	do {
		$subInput = Read-Host 'Please enter a number for your selection or substring for filter'
		if ([string]::IsNullOrWhiteSpace($subInput)) {
			continue
		}

		$parsedSubIndex = 0
		$parsedIsInt = [int]::TryParse($subInput, [ref]$parsedSubIndex)
		if (-not $parsedIsInt) {
			# treat as filter text; show filtered list then re-prompt using the same input message
			$currentSubs = $subscriptions | Where-Object { $_.name -like "*${subInput}*" -or $_.id -like "*${subInput}*" }
			if (-not $currentSubs -or $currentSubs.Count -eq 0) {
				Write-Host 'No subscriptions match that filter. Try again.' -ForegroundColor Yellow
				$currentSubs = $subscriptions
				continue
			}
			Write-Host 'Filtered subscriptions:'
			for ($i = 0; $i -lt $currentSubs.Count; $i++) {
				$sub = $currentSubs[$i]
				Write-Host ("{0,2}. {1} ({2})" -f $i, $sub.name, $sub.id)
			}
			continue
		}
		if ($parsedSubIndex -lt 0 -or $parsedSubIndex -ge $currentSubs.Count) {
			Write-Host 'Invalid subscription number. Try again.' -ForegroundColor Yellow
			continue
		}
		$subIndex = $parsedSubIndex
	} while ($null -eq $subIndex)

	$selectedSub = $currentSubs[[int]$subIndex]
	Write-Host "Selected subscription: $($selectedSub.name) ($($selectedSub.id))"

	Write-Host 'Fetching regions for the subscription...'
	$locations = $null
	# First attempt: use --subscription (stderr suppressed to avoid noise on older CLIs)
	$locationsJson = az account list-locations --subscription $selectedSub.id 2>$null
	if (-not [string]::IsNullOrWhiteSpace($locationsJson)) {
		$locations = $locationsJson | ConvertFrom-Json
	}

	# Fallback for CLI variants that ignore/deny --subscription
	if (-not $locations -or $locations.Count -eq 0) {
		$originalSubId = $null
		try {
			$originalSubId = az account show --query id -o tsv 2>$null
		} catch {
			$originalSubId = $null
		}

		az account set --subscription $selectedSub.id | Out-Null
		try {
			$locationsJson = az account list-locations 2>$null
			if (-not [string]::IsNullOrWhiteSpace($locationsJson)) {
				$locations = $locationsJson | ConvertFrom-Json
			}
		} finally {
			if ($originalSubId -and $originalSubId -ne $selectedSub.id) {
				az account set --subscription $originalSubId | Out-Null
			}
		}
	}

	if (-not $locations -or $locations.Count -eq 0) {
		Write-Host 'No regions returned. Ensure you are logged in and have access to this subscription.' -ForegroundColor Yellow
		Write-Host "Try: 'az login' (if needed) and 'az account list-locations --subscription $($selectedSub.id) -o table' to verify." -ForegroundColor Yellow
		throw 'No regions found for the selected subscription.'
	}

	Write-Host 'Regions:'
	for ($i = 0; $i -lt $locations.Count; $i++) {
		$loc = $locations[$i]
		Write-Host ("{0,2}. {1} ({2})" -f $i, $loc.displayName, $loc.name)
	}

	# Combined filter/selection loop for regions (single prompt)
	$locIndex = $null
	$currentLocs = $locations
	do {
		$locInput = Read-Host 'Please enter a number for your selection or substring for filter (e.g., eastus)'
		if ([string]::IsNullOrWhiteSpace($locInput)) {
			continue
		}

		$parsedLocIndex = 0
		$parsedIsInt = [int]::TryParse($locInput, [ref]$parsedLocIndex)
		if (-not $parsedIsInt) {
			# treat as filter text; show filtered list then re-prompt using the same input message
			$currentLocs = $locations | Where-Object { $_.displayName -like "*${locInput}*" -or $_.name -like "*${locInput}*" }
			if (-not $currentLocs -or $currentLocs.Count -eq 0) {
				Write-Host 'No regions match that filter. Try again.' -ForegroundColor Yellow
				$currentLocs = $locations
				continue
			}
			Write-Host 'Filtered regions:'
			for ($i = 0; $i -lt $currentLocs.Count; $i++) {
				$loc = $currentLocs[$i]
				Write-Host ("{0,2}. {1} ({2})" -f $i, $loc.displayName, $loc.name)
			}
			continue
		}
		if ($parsedLocIndex -lt 0 -or $parsedLocIndex -ge $currentLocs.Count) {
			Write-Host 'Invalid region number. Try again.' -ForegroundColor Yellow
			continue
		}
		$locIndex = $parsedLocIndex
	} while ($null -eq $locIndex)

	$selectedLoc = $currentLocs[[int]$locIndex].name
	Write-Host "Selected region: $selectedLoc"
}

# Show quota/usage for the selected region
Write-Host "Fetching quota/usage for $selectedLoc..."
$usages = @()

# Try primary call
try {
	$raw = az cognitiveservices usage list --subscription $selectedSub.id --location $selectedLoc 2>$null
	if (-not [string]::IsNullOrWhiteSpace($raw)) { $usages = $raw | ConvertFrom-Json }
} catch { $usages = @() }

# Fallbacks: some CLI versions need kind
if (-not $usages -or $usages.Count -eq 0) {
	try {
		$raw = az cognitiveservices usage list --subscription $selectedSub.id --location $selectedLoc --kind OpenAI 2>$null
		if (-not [string]::IsNullOrWhiteSpace($raw)) { $usages = $raw | ConvertFrom-Json }
	} catch { $usages = @() }
}

if (-not $usages -or $usages.Count -eq 0) {
	try {
		$raw = az cognitiveservices usage list --subscription $selectedSub.id --location $selectedLoc --kind AIServices 2>$null
		if (-not [string]::IsNullOrWhiteSpace($raw)) { $usages = $raw | ConvertFrom-Json }
	} catch { $usages = @() }
}

if (-not $usages -or $usages.Count -eq 0) {
	Write-Host 'No quota/usage data returned (or not supported by your CLI/permissions). You can verify with:' -ForegroundColor Yellow
	Write-Host "  az cognitiveservices usage list --subscription $($selectedSub.id) --location $selectedLoc -o table" -ForegroundColor Yellow
	Write-Host "  az cognitiveservices usage list --subscription $($selectedSub.id) --location $selectedLoc --kind OpenAI -o table" -ForegroundColor Yellow
	Write-Host "  az cognitiveservices usage list --subscription $($selectedSub.id) --location $selectedLoc --kind AIServices -o table" -ForegroundColor Yellow
	Write-Host 'Subscription and region saved. Exiting.'
	exit 0
}

function Show-ModelList {
	param(
		[Parameter(Mandatory)] [array] $Models,
		[int] $StartIndex = 0
	)
	for ($i = 0; $i -lt $Models.Count; $i++) {
		$u = $Models[$i]
		$name = if ($u.PSObject.Properties['name']) {
			if ($u.name.PSObject.Properties['value']) { $u.name.value } else { $u.name }
		} else { 'unknown' }
		$hasCurrent = $u.PSObject.Properties['currentValue']
		$hasLimit = $u.PSObject.Properties['limit']
		$current = if ($hasCurrent) { [decimal]$u.currentValue } else { $null }
		$limit = if ($hasLimit) { [decimal]$u.limit } else { $null }
		$available = if ($current -ne $null -and $limit -ne $null) { $limit - $current } else { $null }
		if ($current -ne $null -or $limit -ne $null) {
			$line = "{0,2}. {1} | used: {2} | limit: {3}" -f ($i + $StartIndex), $name, ($current ?? 'n/a'), ($limit ?? 'n/a')
			if ($available -ne $null) { $line += " | available: $available" }
			
			# Show in red if available is 0
			if ($available -eq 0) {
				Write-Host $line -ForegroundColor Red
			} else {
				Write-Host $line
			}
		} else {
			# Fallback: emit raw usage object when expected fields are absent
			$raw = $u | ConvertTo-Json -Compress
			Write-Host ("{0,2}. {1} | raw: {2}" -f ($i + $StartIndex), $name, $raw)
		}
	}
}

function Select-Model {
	param(
		[Parameter(Mandatory)] [array] $Models,
		[Parameter(Mandatory)] [string] $Prompt,
		[bool] $AllowSkip = $false
	)
	
	$modelIndex = $null
	$currentModels = $Models
	do {
		$modelInput = Read-Host $Prompt
		if ([string]::IsNullOrWhiteSpace($modelInput)) {
			if ($AllowSkip) {
				return $null
			}
			Write-Host 'Please enter a valid number or filter string.' -ForegroundColor Yellow
			continue
		}

		$parsedModelIndex = 0
		$parsedIsInt = [int]::TryParse($modelInput, [ref]$parsedModelIndex)
		if (-not $parsedIsInt) {
			# treat as filter text; show filtered list then re-prompt
			$currentModels = $Models | Where-Object { 
				$modelName = if ($_.PSObject.Properties['name']) {
					if ($_.name.PSObject.Properties['value']) { $_.name.value } else { $_.name }
				} else { 'unknown' }
				$modelName -like "*${modelInput}*"
			}
			if (-not $currentModels -or $currentModels.Count -eq 0) {
				Write-Host 'No models match that filter. Try again.' -ForegroundColor Yellow
				$currentModels = $Models
				continue
			}
			Write-Host 'Filtered models:'
			Show-ModelList -Models $currentModels
			continue
		}
		if ($parsedModelIndex -lt 0 -or $parsedModelIndex -ge $currentModels.Count) {
			Write-Host 'Invalid model number. Try again.' -ForegroundColor Yellow
			continue
		}
		$modelIndex = $parsedModelIndex
	} while ($null -eq $modelIndex)
	
	return $currentModels[[int]$modelIndex]
}

function Parse-ModelName {
	param(
		[Parameter(Mandatory)] [string] $ModelName
	)
	
	$result = @{
		Name = $ModelName
		Format = ''
		Sku = ''
		Version = ''
	}
	
	if ($ModelName -match '^([^.]+)\.([^.]+)\.([^.]+)\.(.+)$') {
		# Format with version: OpenAI.Standard.text-embedding-3-small.1
		$result.Format = $Matches[1]
		$result.Sku = $Matches[2]
		$result.Name = $Matches[3]
		$result.Version = $Matches[4]
	} elseif ($ModelName -match '^([^.]+)\.([^.]+)\.(.+)$') {
		# Format without version: OpenAI.Standard.text-embedding-3-small
		$result.Format = $Matches[1]
		$result.Sku = $Matches[2]
		$result.Name = $Matches[3]
	} else {
		Write-Host "Model name does not match expected format. Using as-is: $ModelName" -ForegroundColor Yellow
	}
	
	return $result
}

Write-Host 'Quota/Usage (Available Models):'
Show-ModelList -Models $usages

# Agent model selection
$selectedModel = Select-Model -Models $usages -Prompt 'Please enter a number to select an agent model or substring to filter (e.g., gpt-5)'

$modelName = if ($selectedModel.PSObject.Properties['name']) {
	if ($selectedModel.name.PSObject.Properties['value']) { $selectedModel.name.value } else { $selectedModel.name }
} else { 'unknown' }

$parsed = Parse-ModelName -ModelName $modelName
if ($parsed.Format -or $parsed.Sku) {
	Write-Host "Parsed model - Format: $($parsed.Format), SKU: $($parsed.Sku), Name: $($parsed.Name)"
}
Write-Host "Selected model: $($parsed.Name)"

# Fetch available versions for the selected model
Write-Host "Fetching available versions for $($parsed.Name) with SKU $($parsed.Sku)..."
$modelVersions = @()
try {
	$raw = az cognitiveservices model list --subscription $selectedSub.id --location $selectedLoc 2>$null
	if (-not [string]::IsNullOrWhiteSpace($raw)) {
		$allModels = $raw | ConvertFrom-Json
		$nameMatches = $allModels | Where-Object { $_.model.name -eq $parsed.Name }
		$modelVersions = $nameMatches | Where-Object { 
			$_.model.format -eq $parsed.Format -and
			@($_.model.skus | Where-Object { $_.name -eq $parsed.Sku }).Count -gt 0
		}
		$modelVersions = $modelVersions | Sort-Object { $_.model.version } -Unique
	}
} catch {
	$modelVersions = @()
}

$selectedVersion = ''
if ($modelVersions -and $modelVersions.Count -gt 0) {
	Write-Host "Available versions for $($parsed.Name):"
	for ($i = 0; $i -lt $modelVersions.Count; $i++) {
		$ver = $modelVersions[$i].model.version
		Write-Host ("{0,2}. {1}" -f $i, $ver)
	}
	
	$versionIndex = $null
	do {
		$versionInput = Read-Host 'Please enter a number to select a version'
		if ([string]::IsNullOrWhiteSpace($versionInput)) {
			Write-Host 'Please enter a valid number.' -ForegroundColor Yellow
			continue
		}
		
		$parsedVerIndex = 0
		if ([int]::TryParse($versionInput, [ref]$parsedVerIndex)) {
			if ($parsedVerIndex -ge 0 -and $parsedVerIndex -lt $modelVersions.Count) {
				$selectedVersion = $modelVersions[$parsedVerIndex].model.version
				$versionIndex = $parsedVerIndex
			} else {
				Write-Host 'Invalid version number. Try again.' -ForegroundColor Yellow
			}
		} else {
			Write-Host 'Please enter a valid number.' -ForegroundColor Yellow
		}
	} while ($null -eq $versionIndex)
	
	Write-Host "Selected version: $selectedVersion"
} else {
	Write-Host "No version information available for this model." -ForegroundColor Yellow
}

# Embedding model selection
Write-Host ''
Write-Host 'Embedding Model Selection (for AI Search):'
Show-ModelList -Models $usages

$selectedEmbedModel = Select-Model -Models $usages -Prompt 'Please enter a number to select an embedding model or substring to filter (or press Enter to skip provisioning AI Search)' -AllowSkip $true

if ($null -ne $selectedEmbedModel) {
	$embedModelName = if ($selectedEmbedModel.PSObject.Properties['name']) {
		if ($selectedEmbedModel.name.PSObject.Properties['value']) { $selectedEmbedModel.name.value } else { $selectedEmbedModel.name }
	} else { 'unknown' }

	$embedParsed = Parse-ModelName -ModelName $embedModelName
	if ($embedParsed.Format -or $embedParsed.Sku -or $embedParsed.Version) {
		Write-Host "Parsed embedding model - Format: $($embedParsed.Format), SKU: $($embedParsed.Sku), Name: $($embedParsed.Name)$(if($embedParsed.Version){", Version: $($embedParsed.Version)"})"
	}
	Write-Host "Selected embedding model: $($embedParsed.Name)"

	# Fetch available versions for the selected embedding model
	Write-Host "Fetching available versions for $($embedParsed.Name) with SKU $($embedParsed.Sku)..."
	$embedVersions = @()
	try {
		$raw = az cognitiveservices model list --subscription $selectedSub.id --location $selectedLoc 2>$null
		if (-not [string]::IsNullOrWhiteSpace($raw)) {
			$allModels = $raw | ConvertFrom-Json
			$embedVersions = $allModels | Where-Object { 
				$_.model.name -eq $embedParsed.Name -and 
				$_.model.format -eq $embedParsed.Format -and
				@($_.model.skus | Where-Object { $_.name -eq $embedParsed.Sku }).Count -gt 0
			}
			$embedVersions = $embedVersions | Sort-Object { $_.model.version } -Unique
		}
	} catch {
		$embedVersions = @()
	}

	$selectedEmbedVersion = ''
	if ($embedVersions -and $embedVersions.Count -gt 0) {
		Write-Host "Available versions for $($embedParsed.Name):"
		for ($i = 0; $i -lt $embedVersions.Count; $i++) {
			$ver = $embedVersions[$i].model.version
			Write-Host ("{0,2}. {1}" -f $i, $ver)
		}
		
		$embedVerIndex = $null
		do {
			$embedVerInput = Read-Host 'Please enter a number to select a version'
			if ([string]::IsNullOrWhiteSpace($embedVerInput)) {
				Write-Host 'Please enter a valid number.' -ForegroundColor Yellow
				continue
			}
			
			$parsedEmbedVerIndex = 0
			if ([int]::TryParse($embedVerInput, [ref]$parsedEmbedVerIndex)) {
				if ($parsedEmbedVerIndex -ge 0 -and $parsedEmbedVerIndex -lt $embedVersions.Count) {
					$selectedEmbedVersion = $embedVersions[$parsedEmbedVerIndex].model.version
					$embedVerIndex = $parsedEmbedVerIndex
				} else {
					Write-Host 'Invalid version number. Try again.' -ForegroundColor Yellow
				}
			} else {
				Write-Host 'Please enter a valid number.' -ForegroundColor Yellow
			}
		} while ($null -eq $embedVerIndex)
		
		Write-Host "Selected version: $selectedEmbedVersion"
	} else {
		Write-Host "No version information available for this model." -ForegroundColor Yellow
	}
} else {
	Write-Host 'Skipping embedding model selection. AI Search will not be provisioned.' -ForegroundColor Yellow
}

# Save all selections at the end
Write-Host ''
Write-Host 'Saving all selections to azd environment...'

# Save subscription and region
azd env set AZURE_SUBSCRIPTION_ID $selectedSub.id | Out-Null
azd env set AZURE_LOCATION $selectedLoc | Out-Null

# Save agent model
azd env set AZURE_AI_AGENT_MODEL_NAME $parsed.Name | Out-Null
if ($parsed.Format) { azd env set AZURE_AI_AGENT_MODEL_FORMAT $parsed.Format | Out-Null }
if ($parsed.Sku) { azd env set AZURE_AI_AGENT_DEPLOYMENT_SKU $parsed.Sku | Out-Null }
if ($selectedVersion) { azd env set AZURE_AI_AGENT_MODEL_VERSION $selectedVersion | Out-Null }

# Save embedding model (if selected)
if ($null -ne $selectedEmbedModel) {
	azd env set AZURE_AI_EMBED_MODEL_NAME $embedParsed.Name | Out-Null
	if ($embedParsed.Format) { azd env set AZURE_AI_EMBED_MODEL_FORMAT $embedParsed.Format | Out-Null }
	if ($embedParsed.Sku) { azd env set AZURE_AI_EMBED_DEPLOYMENT_SKU $embedParsed.Sku | Out-Null }
	if ($selectedEmbedVersion) { azd env set AZURE_AI_EMBED_MODEL_VERSION $selectedEmbedVersion | Out-Null }
	azd env set USE_AZURE_AI_SEARCH_SERVICE 'true' | Out-Null
} else {
	azd env set USE_AZURE_AI_SEARCH_SERVICE 'false' | Out-Null
}

Write-Host "Done. All selections saved."

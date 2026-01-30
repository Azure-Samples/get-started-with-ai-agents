<#
	Prompts to select an Azure subscription and region, then writes them
	to the active azd environment as AZURE_SUBSCRIPTION_ID and AZURE_LOCATION.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'


# for any unhandled errors or ctrl-c, exit with code 1
trap {
	exit 1
}

function Ensure-Command {
	param(
		[Parameter(Mandatory)] [string] $Name
	)
	if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
		throw "Required command '$Name' not found. Install it and retry."
	}
}

function Show-InteractiveMenu {
	param(
		[Parameter(Mandatory)] [array] $Items,
		[Parameter(Mandatory)] [string] $Title,
		[Parameter(Mandatory)] [scriptblock] $DisplayProperty,
		[scriptblock] $FilterProperty,
		[scriptblock] $ColorProperty,
		[string[]] $ContextLines,
		[bool] $AllowSkip = $false
	)
	
	if (-not $Items -or $Items.Count -eq 0) {
		throw "No items to display"
	}
	
	$filteredItems = $Items
	$selected = 0
	$filterText = ""
	$escape = $false
	$previousFilteredCount = $filteredItems.Count
	$needsFullRedraw = $true
	
	while (-not $escape) {
		# Get console width for padding
		$consoleWidth = $Host.UI.RawUI.WindowSize.Width
		
		# Only clear screen when filter changes (different result count) or first draw
		if ($needsFullRedraw -or $filteredItems.Count -ne $previousFilteredCount) {
			Clear-Host
			$previousFilteredCount = $filteredItems.Count
			$needsFullRedraw = $false
		} else {
			# Just reposition cursor for navigation
			[Console]::SetCursorPosition(0, 0)
		}
		
		# Display context/previous selections at the top
		if ($ContextLines -and $ContextLines.Count -gt 0) {
			Write-Host "Selected so far:" -ForegroundColor DarkGray
			foreach ($line in $ContextLines) {
				Write-Host "  $line" -ForegroundColor DarkGray
			}
			Write-Host ""
		}
		
		Write-Host $Title -ForegroundColor Cyan
		
		# Show filter text if active
		if ($filterText) {
			Write-Host "Filter: $filterText" -ForegroundColor Yellow
		}
		
		Write-Host ""
		
		$displayCount = [Math]::Min(20, $filteredItems.Count)
		$startIdx = [Math]::Max(0, $selected - 10)
		$endIdx = [Math]::Min($filteredItems.Count - 1, $startIdx + $displayCount - 1)
		
		if ($filteredItems.Count -eq 0) {
			Write-Host "  No matches found." -ForegroundColor Yellow
		}
		
		for ($i = $startIdx; $i -le $endIdx; $i++) {
			$displayText = & $DisplayProperty $filteredItems[$i] $i
			
			$color = if ($ColorProperty) { & $ColorProperty $filteredItems[$i] } else { $null }
			
			# Pad line to console width to overwrite old content
			$prefix = if ($i -eq $selected) { "  > " } else { "    " }
			$fullLine = "$prefix$displayText"
			if ($fullLine.Length -lt $consoleWidth) {
				$fullLine = $fullLine.PadRight($consoleWidth)
			}
			
			if ($i -eq $selected) {
				if ($color -eq 'Red') {
					Write-Host $fullLine -ForegroundColor DarkRed -NoNewline
				} else {
					Write-Host $fullLine -ForegroundColor Green -NoNewline
				}
			} elseif ($color) {
				Write-Host $fullLine -ForegroundColor $color -NoNewline
			} else {
				Write-Host $fullLine -NoNewline
			}
			Write-Host "" # Newline
		}
		
		# Pad empty lines to fill the display area
		$linesShown = $endIdx - $startIdx + 1
		$maxLines = [Math]::Min(20, $filteredItems.Count)
		if ($filteredItems.Count -eq 0) {
			$linesShown = 1
			$maxLines = 20
		}
		for ($i = $linesShown; $i -lt $maxLines; $i++) {
			Write-Host ("".PadRight($consoleWidth))
		}
		
		Write-Host ""
		if ($AllowSkip) {
			Write-Host "↑↓: Navigate | Enter: Select | Type: Filter | Esc: Skip" -ForegroundColor DarkGray
		} else {
			Write-Host "↑↓: Navigate | Enter: Select | Type: Filter | Esc: Clear" -ForegroundColor DarkGray
		}
		
		$key = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
		
		# Check for Ctrl+C (VirtualKeyCode 3 when TreatControlCAsInput is true)
		if ($key.VirtualKeyCode -eq 3 -or
		    (($key.VirtualKeyCode -eq 67) -and 
		     (($key.ControlKeyState -band [System.Management.Automation.Host.ControlKeyStates]::LeftCtrlPressed) -or
		      ($key.ControlKeyState -band [System.Management.Automation.Host.ControlKeyStates]::RightCtrlPressed)))) {
			[Console]::TreatControlCAsInput = $false
			Clear-Host
			Write-Host ""
			Write-Host "Operation cancelled by user." -ForegroundColor Yellow
			Write-Host ""
			exit 1
		}
		
		switch ($key.VirtualKeyCode) {
			38 { # Up arrow
				if ($selected -gt 0) {
					$selected--
				}
			}
			40 { # Down arrow
				if ($selected -lt $filteredItems.Count - 1) {
					$selected++
				}
			}
			13 { # Enter
				$escape = $true
			}
			27 { # Escape - skip or clear filter
				if ($AllowSkip -and -not $filterText) {
					# Skip selection
					$escape = $true
					$selected = -1
				} elseif ($filterText) {
					# Clear filter
					$filterText = ""
					$filteredItems = $Items
					$selected = 0
					$needsFullRedraw = $true
				}
			}
			8 { # Backspace
				if ($filterText.Length -gt 0) {
					$filterText = $filterText.Substring(0, $filterText.Length - 1)
					if ($FilterProperty) {
						$filteredItems = $Items | Where-Object { & $FilterProperty $_ $filterText }
					}
					if (-not $filteredItems -or $filteredItems.Count -eq 0) {
						$filteredItems = $Items
						$filterText = ""
					}
					$selected = 0
					$needsFullRedraw = $true
				}
			}
			default {
				if ($key.Character -match '[a-zA-Z0-9\-\s\.\|:\(\)_]') {
					$filterText += $key.Character
					if ($FilterProperty) {
						$filteredItems = $Items | Where-Object { & $FilterProperty $_ $filterText }
					}
					if (-not $filteredItems -or $filteredItems.Count -eq 0) {
						$filteredItems = @()
					}
					$selected = 0
					$needsFullRedraw = $true
				}
			}
		}
	}
	
	if ($selected -eq -1) {
		return $null
	}
	return $filteredItems[$selected]
}

Ensure-Command -Name az
Ensure-Command -Name azd

# Initialize context tracking for all selections
$contextLines = @()

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
	
	$selectedSub = Show-InteractiveMenu -Items $subscriptions -Title "Select Azure Subscription" `
		-DisplayProperty { param($sub, $idx) "$($sub.name) ($($sub.id))" } `
		-FilterProperty { param($sub, $filter) $sub.name -like "*$filter*" -or $sub.id -like "*$filter*" } `
		-ContextLines $contextLines
	
	Clear-Host
	Write-Host "Selected subscription: $($selectedSub.name) ($($selectedSub.id))"
	$contextLines += "Subscription: $($selectedSub.name)"

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

	$selectedLocObj = Show-InteractiveMenu -Items $locations -Title "Select Azure Region" `
		-DisplayProperty { param($loc, $idx) "$($loc.displayName) ($($loc.name))" } `
		-FilterProperty { param($loc, $filter) $loc.displayName -like "*$filter*" -or $loc.name -like "*$filter*" } `
		-ContextLines $contextLines
	
	Clear-Host
	Write-Host "Selected subscription: $($selectedSub.name)"
	$selectedLoc = $selectedLocObj.name
	Write-Host "Selected region: $selectedLoc"
	$contextLines[0] = "Subscription: $($selectedSub.name) | Region: $selectedLoc"
	
	# Get the azd environment name
	$envName = azd env get-value AZURE_ENV_NAME 2>$null
	if ([string]::IsNullOrWhiteSpace($envName)) {
		$envName = (Get-Location | Split-Path -Leaf)
	}
	
	# Prompt for resource group name with default suggestion
	$defaultRgName = "rg-$envName"
	Write-Host ""
	Write-Host "Resource Group Name" -ForegroundColor Cyan
	$rgName = Read-Host "Enter resource group name (press Enter to use default: $defaultRgName)"
	if ([string]::IsNullOrWhiteSpace($rgName)) {
		$rgName = $defaultRgName
	}
	Write-Host "Resource group: $rgName"
	$contextLines[0] += " | RG: $rgName"
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
	Write-Host ''
	Write-Host 'No quota/usage data returned (or not supported by your CLI/permissions). You can verify with:' -ForegroundColor Yellow
	Write-Host "  az cognitiveservices usage list --subscription $($selectedSub.id) --location $selectedLoc -o table" -ForegroundColor Yellow
	Write-Host "  az cognitiveservices usage list --subscription $($selectedSub.id) --location $selectedLoc --kind OpenAI -o table" -ForegroundColor Yellow
	Write-Host "  az cognitiveservices usage list --subscription $($selectedSub.id) --location $selectedLoc --kind AIServices -o table" -ForegroundColor Yellow
	Write-Host ''
	Write-Host 'No models available in this region. Please select a different region.' -ForegroundColor Red
	Write-Host ''
	exit 1
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
		
		# Parse model name to extract format, sku, and model name
		$displayName = $name
		$sku = ''
		if ($name -match '^([^.]+)\.([^.]+)\.(.+)$') {
			# Format: OpenAI.GlobalStandard.gpt-5
			$displayName = $Matches[3]
			$sku = $Matches[2]
		}
		
		if ($current -ne $null -or $limit -ne $null) {
			$line = "{0}" -f $displayName
			if ($sku) { $line += " | $sku" }
			$line += " | used: {0} | limit: {1}" -f ($current ?? 'n/a'), ($limit ?? 'n/a')
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
			Write-Host ("{0} | raw: {1}" -f $displayName, $raw)
		}
	}
}

function Select-Model {
	param(
		[Parameter(Mandatory)] [array] $Models,
		[Parameter(Mandatory)] [string] $Title,
		[bool] $AllowSkip = $false,
		[string[]] $ContextLines
	)
	
	$selectedModel = Show-InteractiveMenu -Items $Models -Title $Title `
		-ContextLines $ContextLines `
		-AllowSkip $AllowSkip `
		-DisplayProperty { 
			param($u, $idx)
			$u.DisplayText
		} `
		-FilterProperty { 
			param($u, $filter)
			$u.DisplayText -like "*$filter*"
		} `
		-ColorProperty {
			param($u)
			$hasCurrent = $u.PSObject.Properties['currentValue']
			$hasLimit = $u.PSObject.Properties['limit']
			$current = if ($hasCurrent) { [decimal]$u.currentValue } else { $null }
			$limit = if ($hasLimit) { [decimal]$u.limit } else { $null }
			$available = if ($current -ne $null -and $limit -ne $null) { $limit - $current } else { $null }
			
			if ($available -eq 0) { 'Red' } else { $null }
		}
	
	return $selectedModel
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

# Add display text to models and sort by display text
$finalUsage = $usages | ForEach-Object {
	$u = $_
	$name = if ($u.PSObject.Properties['name']) {
		if ($u.name.PSObject.Properties['value']) { $u.name.value } else { $u.name }
	} else { 'unknown' }
	$hasCurrent = $u.PSObject.Properties['currentValue']
	$hasLimit = $u.PSObject.Properties['limit']
	$current = if ($hasCurrent) { [decimal]$u.currentValue } else { $null }
	$limit = if ($hasLimit) { [decimal]$u.limit } else { $null }
	$available = if ($current -ne $null -and $limit -ne $null) { $limit - $current } else { $null }
	
	# Parse model name to extract display name and sku
	$displayName = $name
	$sku = ''
	if ($name -match '^([^.]+)\.([^.]+)\.(.+)$') {
		$displayName = $Matches[3]
		$sku = $Matches[2]
	}
	
	# Build display text
	$displayText = "$displayName"
	if ($sku) { $displayText += " | $sku" }
	$displayText += " | used: $($current ?? 'n/a') | limit: $($limit ?? 'n/a')"
	if ($available -ne $null) { $displayText += " | available: $available" }
	
	# Add DisplayText property to the object
	$u | Add-Member -NotePropertyName 'DisplayText' -NotePropertyValue $displayText -Force -PassThru
} | Sort-Object DisplayText

# Agent model selection
$selectedModel = Select-Model -Models $finalUsage -Title "Select Agent Model (hint: filter by 'gpt')" -ContextLines $contextLines

$modelName = if ($selectedModel.PSObject.Properties['name']) {
	if ($selectedModel.name.PSObject.Properties['value']) { $selectedModel.name.value } else { $selectedModel.name }
} else { 'unknown' }

$parsed = Parse-ModelName -ModelName $modelName
if ($parsed.Format -or $parsed.Sku) {
	Write-Host "Parsed model - Format: $($parsed.Format), SKU: $($parsed.Sku), Name: $($parsed.Name)"
}

# Add placeholder to context
$contextLines += "Agent Model: ..."

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
		$modelVersions = $modelVersions | Sort-Object { $_.model.version } -Descending -Unique
	}
} catch {
	$modelVersions = @()
}

$selectedVersion = ''
if ($modelVersions -and $modelVersions.Count -gt 0) {
	$selectedVersionObj = Show-InteractiveMenu -Items $modelVersions -Title "Select Version for $($parsed.Name)" `
		-DisplayProperty { param($v, $idx) $v.model.version } `
		-FilterProperty { param($v, $filter) $v.model.version -like "*$filter*" } `
		-ContextLines $contextLines
	
	$selectedVersion = $selectedVersionObj.model.version
} else {
	Write-Host "No version information available for this model." -ForegroundColor Yellow
}

# Get quota available for agent model
$agentCurrent = if ($selectedModel.PSObject.Properties['currentValue']) { [decimal]$selectedModel.currentValue } else { 0 }
$agentLimit = if ($selectedModel.PSObject.Properties['limit']) { [decimal]$selectedModel.limit } else { 0 }
$agentAvailable = if ($agentLimit -gt 0) { $agentLimit - $agentCurrent } else { 'n/a' }

# Prompt for agent capacity
Write-Host ""
$agentCapacity = Read-Host "Enter capacity for agent model (quota available: $agentAvailable, press Enter for default: 80)"
if ([string]::IsNullOrWhiteSpace($agentCapacity)) {
	$agentCapacity = "80"
}

Write-Host "Selected: $($parsed.Name) v$selectedVersion | capacity: $agentCapacity" -ForegroundColor Green
$contextLines[-1] = "Agent Model: $($parsed.Name) v$selectedVersion | capacity: $agentCapacity"

# Embedding model selection
Write-Host ''
Write-Host 'Embedding Model Selection (for AI Search):'

$selectedEmbedModel = Select-Model -Models $finalUsage -Title "Select Embedding Model for AI Search (hint: filter by 'embedding' or press Esc to skip)" -AllowSkip $true -ContextLines $contextLines

if ($null -ne $selectedEmbedModel) {
	$embedModelName = if ($selectedEmbedModel.PSObject.Properties['name']) {
		if ($selectedEmbedModel.name.PSObject.Properties['value']) { $selectedEmbedModel.name.value } else { $selectedEmbedModel.name }
	} else { 'unknown' }

	$embedParsed = Parse-ModelName -ModelName $embedModelName
	if ($embedParsed.Format -or $embedParsed.Sku -or $embedParsed.Version) {
		Write-Host "Parsed embedding model - Format: $($embedParsed.Format), SKU: $($embedParsed.Sku), Name: $($embedParsed.Name)$(if($embedParsed.Version){", Version: $($embedParsed.Version)"})"
	}
	Write-Host "Selected embedding model: $($embedParsed.Name)"
	$contextLines += "Embedding Model: ..."

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
			$embedVersions = $embedVersions | Sort-Object { $_.model.version } -Descending -Unique
		}
	} catch {
		$embedVersions = @()
	}

	$selectedEmbedVersion = ''
	if ($embedVersions -and $embedVersions.Count -gt 0) {
		$selectedEmbedVersionObj = Show-InteractiveMenu -Items $embedVersions -Title "Select Version for $($embedParsed.Name)" `
			-DisplayProperty { param($v, $idx) $v.model.version } `
			-FilterProperty { param($v, $filter) $v.model.version -like "*$filter*" } `
			-ContextLines $contextLines
		
		$selectedEmbedVersion = $selectedEmbedVersionObj.model.version
	} else {
		Write-Host "No version information available for this model." -ForegroundColor Yellow
	}
	
	# Get quota available for embedding model
	$embedCurrent = if ($selectedEmbedModel.PSObject.Properties['currentValue']) { [decimal]$selectedEmbedModel.currentValue } else { 0 }
	$embedLimit = if ($selectedEmbedModel.PSObject.Properties['limit']) { [decimal]$selectedEmbedModel.limit } else { 0 }
	$embedAvailable = if ($embedLimit -gt 0) { $embedLimit - $embedCurrent } else { 'n/a' }
	
	# Prompt for embedding capacity
	Write-Host ""
	$embedCapacity = Read-Host "Enter capacity for embedding model (quota available: $embedAvailable, press Enter for default: 50)"
	if ([string]::IsNullOrWhiteSpace($embedCapacity)) {
		$embedCapacity = "50"
	}
	
	Write-Host "Selected: $($embedParsed.Name) v$selectedEmbedVersion | capacity: $embedCapacity" -ForegroundColor Green
	$contextLines[-1] = "Embedding Model: $($embedParsed.Name) v$selectedEmbedVersion | capacity: $embedCapacity"
} else {
	Write-Host 'Skipping embedding model selection. AI Search will not be provisioned.' -ForegroundColor Yellow
}

# Additional models selection (loop until ESC)
Write-Host ''
Write-Host 'Additional Models Selection:'
Write-Host 'You can now select additional models to provision. Press ESC when done.' -ForegroundColor Cyan
$additionalModels = @()

while ($true) {
	Write-Host ''
	
	$selectedAdditionalModel = Select-Model -Models $finalUsage -Title "Select Additional Model (or press Esc to finish)" -AllowSkip $true -ContextLines $contextLines
	
	if ($null -eq $selectedAdditionalModel) {
		Write-Host 'No more models to add. Proceeding...' -ForegroundColor Yellow
		break
	}
	
	$additionalModelName = if ($selectedAdditionalModel.PSObject.Properties['name']) {
		if ($selectedAdditionalModel.name.PSObject.Properties['value']) { $selectedAdditionalModel.name.value } else { $selectedAdditionalModel.name }
	} else { 'unknown' }
	
	$additionalParsed = Parse-ModelName -ModelName $additionalModelName
	if ($additionalParsed.Format -or $additionalParsed.Sku) {
		Write-Host "Parsed additional model - Format: $($additionalParsed.Format), SKU: $($additionalParsed.Sku), Name: $($additionalParsed.Name)"
	}
	Write-Host "Selected additional model: $($additionalParsed.Name)"
	$contextLines += "Additional Model: ..."
	
	# Fetch available versions for the additional model
	Write-Host "Fetching available versions for $($additionalParsed.Name) with SKU $($additionalParsed.Sku)..."
	$additionalVersions = @()
	try {
		$raw = az cognitiveservices model list --subscription $selectedSub.id --location $selectedLoc 2>$null
		if (-not [string]::IsNullOrWhiteSpace($raw)) {
			$allModels = $raw | ConvertFrom-Json
			$additionalVersions = $allModels | Where-Object { 
				$_.model.name -eq $additionalParsed.Name -and 
				$_.model.format -eq $additionalParsed.Format -and
				@($_.model.skus | Where-Object { $_.name -eq $additionalParsed.Sku }).Count -gt 0
			}
			$additionalVersions = $additionalVersions | Sort-Object { $_.model.version } -Descending -Unique
		}
	} catch {
		$additionalVersions = @()
	}
	
	$selectedAdditionalVersion = ''
	if ($additionalVersions -and $additionalVersions.Count -gt 0) {
		$selectedAdditionalVersionObj = Show-InteractiveMenu -Items $additionalVersions -Title "Select Version for $($additionalParsed.Name)" `
			-DisplayProperty { param($v, $idx) $v.model.version } `
			-FilterProperty { param($v, $filter) $v.model.version -like "*$filter*" } `
			-ContextLines $contextLines
		
		$selectedAdditionalVersion = $selectedAdditionalVersionObj.model.version
	} else {
		Write-Host "No version information available for this model." -ForegroundColor Yellow
	}
	
	# Get quota available for additional model
	$additionalCurrent = if ($selectedAdditionalModel.PSObject.Properties['currentValue']) { [decimal]$selectedAdditionalModel.currentValue } else { 0 }
	$additionalLimit = if ($selectedAdditionalModel.PSObject.Properties['limit']) { [decimal]$selectedAdditionalModel.limit } else { 0 }
	$additionalAvailable = if ($additionalLimit -gt 0) { $additionalLimit - $additionalCurrent } else { 'n/a' }
	
	# Prompt for capacity
	Write-Host ""
	$capacity = Read-Host "Enter capacity for this model (quota available: $additionalAvailable, press Enter for default: 10)"
	if ([string]::IsNullOrWhiteSpace($capacity)) {
		$capacity = "10"
	}
	
	# Create model object
	$modelObj = [ordered]@{
		name = $additionalParsed.Name
		version = $selectedAdditionalVersion
		sku = $additionalParsed.Sku
		format = $additionalParsed.Format
		capacity = $capacity
	}
	
	$additionalModels += $modelObj
	
	Write-Host "Selected: $($additionalParsed.Name) v$selectedAdditionalVersion | capacity: $capacity" -ForegroundColor Green
	$contextLines[-1] = "Additional Model: $($additionalParsed.Name) v$selectedAdditionalVersion | capacity: $capacity"
}

# Save all selections at the end
Write-Host ''
Write-Host 'Saving all selections to azd environment...'

# Save subscription, region, and resource group
azd env set AZURE_SUBSCRIPTION_ID $selectedSub.id | Out-Null
azd env set AZURE_LOCATION $selectedLoc | Out-Null
azd env set AZURE_RESOURCE_GROUP $rgName | Out-Null

# Save agent model
azd env set AZURE_AI_AGENT_MODEL_NAME $parsed.Name | Out-Null
if ($parsed.Format) { azd env set AZURE_AI_AGENT_MODEL_FORMAT $parsed.Format | Out-Null }
if ($parsed.Sku) { azd env set AZURE_AI_AGENT_DEPLOYMENT_SKU $parsed.Sku | Out-Null }
azd env set AZURE_AI_AGENT_MODEL_VERSION $selectedVersion | Out-Null
if ($agentCapacity) { azd env set AZURE_AI_AGENT_DEPLOYMENT_CAPACITY $agentCapacity | Out-Null }

# Save embedding model (if selected)
if ($null -ne $selectedEmbedModel) {
	azd env set AZURE_AI_EMBED_MODEL_NAME $embedParsed.Name | Out-Null
	if ($embedParsed.Format) { azd env set AZURE_AI_EMBED_MODEL_FORMAT $embedParsed.Format | Out-Null }
	if ($embedParsed.Sku) { azd env set AZURE_AI_EMBED_DEPLOYMENT_SKU $embedParsed.Sku | Out-Null }
	azd env set AZURE_AI_EMBED_MODEL_VERSION $selectedEmbedVersion | Out-Null
	if ($embedCapacity) { azd env set AZURE_AI_EMBED_DEPLOYMENT_CAPACITY $embedCapacity | Out-Null }
	azd env set USE_AZURE_AI_SEARCH_SERVICE 'true' | Out-Null
} else {
	azd env set USE_AZURE_AI_SEARCH_SERVICE 'false' | Out-Null
}

# Save additional models as JSON array (always save, even if empty)
if ($additionalModels.Count -gt 0) {
	$jsonArray = $additionalModels | ConvertTo-Json -Compress -Depth 10 -AsArray
} else {
	$jsonArray = '[]'
}
# Escape quotes for environment variable
$escapedJson = $jsonArray -replace '"', '\"'
azd env set AZURE_AI_MODELS $escapedJson | Out-Null
if ($additionalModels.Count -gt 0) {
	Write-Host "Saved $($additionalModels.Count) additional model(s) to AZURE_AI_MODELS"
} else {
	Write-Host "No additional models selected (saved empty array to AZURE_AI_MODELS)"
}

Write-Host "Done. All selections saved."

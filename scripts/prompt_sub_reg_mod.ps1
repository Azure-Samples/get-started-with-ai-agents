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

function Get-AzdEnvValue {
	param(
		[Parameter(Mandatory)] [string] $Key
	)

	$LASTEXITCODE = 0
	$out = ''
	try {
		$out = (azd env get-value $Key 2>$null | Out-String)
	} catch {
		return $null
	}

	# External command failures don't throw; check exit code
	if ($LASTEXITCODE -ne 0) {
		return $null
	}

	$out = $out.Trim()
	if ([string]::IsNullOrWhiteSpace($out)) {
		return $null
	}

	# Some azd versions emit "ERROR: ..." on stdout; treat that as missing
	if ($out -match '^ERROR:\s') {
		return $null
	}

	return $out
}

# Read current azd environment values (use azd directly, but handle missing keys)
$existingSubId = Get-AzdEnvValue -Key 'AZURE_SUBSCRIPTION_ID'
$existingLocation = Get-AzdEnvValue -Key 'AZURE_LOCATION'
$existingRgName = Get-AzdEnvValue -Key 'AZURE_RESOURCE_GROUP'

$existingAgentModelName = Get-AzdEnvValue -Key 'AZURE_AI_AGENT_MODEL_NAME'
$existingAgentModelVersion = Get-AzdEnvValue -Key 'AZURE_AI_AGENT_MODEL_VERSION'
$existingAgentModelCapacity = Get-AzdEnvValue -Key 'AZURE_AI_AGENT_DEPLOYMENT_CAPACITY'

$needsSubscription = [string]::IsNullOrWhiteSpace($existingSubId)
$needsLocation = [string]::IsNullOrWhiteSpace($existingLocation)
$needsResourceGroup = [string]::IsNullOrWhiteSpace($existingRgName)

# Consider the "model" configured only when the core agent model settings exist
$needsAgentModel = (
	[string]::IsNullOrWhiteSpace($existingAgentModelName) -or
	[string]::IsNullOrWhiteSpace($existingAgentModelVersion) -or
	[string]::IsNullOrWhiteSpace($existingAgentModelCapacity)
)

if (-not $needsSubscription -and -not $needsLocation -and -not $needsResourceGroup -and -not $needsAgentModel) {
	Write-Host 'Subscription, region, and model are already configured in the active azd environment.' -ForegroundColor Green
	Write-Host "  Subscription ID: $existingSubId"
	Write-Host "  Location: $existingLocation"
	Write-Host "  Agent model: $existingAgentModelName"
	Write-Host 'No changes needed. Exiting.' -ForegroundColor Green
	exit 0
}

# Resolve env name (used for RG defaults) early
$envName = azd env get-value AZURE_ENV_NAME 2>$null
if ([string]::IsNullOrWhiteSpace($envName)) {
	$envName = (Get-Location | Split-Path -Leaf)
}

# If we need to call Azure for anything, ensure we're logged in
$needsAzureCalls = $needsSubscription -or $needsLocation -or $needsAgentModel
if ($needsAzureCalls) {
	try {
		az account show 1>$null 2>$null
	} catch {
		Write-Host 'Not logged in. Launching az login...' -ForegroundColor Yellow
		az login | Out-Null
	}
}

# Subscription selection/resolution
$selectedSub = $null
if ($needsSubscription) {
	Write-Host 'Fetching subscriptions...'
	$subscriptions = az account list | ConvertFrom-Json | Sort-Object name
	if (-not $subscriptions -or $subscriptions.Count -eq 0) {
		throw 'No subscriptions found for the signed-in account.'
	}
	$selectedSub = Show-InteractiveMenu -Items $subscriptions -Title 'Select Azure Subscription' `
		-DisplayProperty { param($sub, $idx) "$($sub.name) ($($sub.id))" } `
		-FilterProperty { param($sub, $filter) $sub.name -like "*$filter*" -or $sub.id -like "*$filter*" } `
		-ContextLines $contextLines
	Clear-Host
	Write-Host "Selected subscription: $($selectedSub.name) ($($selectedSub.id))"
} else {
	$selectedSub = [pscustomobject]@{ id = $existingSubId; name = $existingSubId }
	# Best-effort: resolve the subscription name for nicer UX
	try {
		$subs = az account list 2>$null | ConvertFrom-Json
		$match = $subs | Where-Object { $_.id -eq $existingSubId } | Select-Object -First 1
		if ($match) { $selectedSub = $match }
	} catch {
		# ignore
	}
}

if ($selectedSub -and $selectedSub.PSObject.Properties['name']) {
	$contextLines += "Subscription: $($selectedSub.name)"
} else {
	$contextLines += "Subscription: $($selectedSub.id)"
}

# Region selection/resolution
$selectedLoc = $existingLocation
if ($needsLocation) {
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

	$selectedLocObj = Show-InteractiveMenu -Items $locations -Title 'Select Azure Region' `
		-DisplayProperty { param($loc, $idx) "$($loc.displayName) ($($loc.name))" } `
		-FilterProperty { param($loc, $filter) $loc.displayName -like "*$filter*" -or $loc.name -like "*$filter*" } `
		-ContextLines $contextLines
	Clear-Host
	$selectedLoc = $selectedLocObj.name
	Write-Host "Selected region: $selectedLoc"
}

if ($contextLines.Count -gt 0) {
	$contextLines[0] = "Subscription: $($selectedSub.name) | Region: $selectedLoc"
} else {
	$contextLines += "Subscription: $($selectedSub.name) | Region: $selectedLoc"
}

# Resource group: prompt only when missing
$rgName = $existingRgName
if ($needsResourceGroup) {
	$defaultRgName = "rg-$envName"
	Write-Host ''
	Write-Host 'Resource Group Name' -ForegroundColor Cyan
	$rgName = Read-Host "Enter resource group name (press Enter to use default: $defaultRgName)"
	if ([string]::IsNullOrWhiteSpace($rgName)) {
		$rgName = $defaultRgName
	}
}

if (-not [string]::IsNullOrWhiteSpace($rgName)) {
	$contextLines[0] += " | RG: $rgName"
}

if ($needsAgentModel) {
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
		[string[]] $ContextLines,
		[string[]] $ExcludedModelNames = @()
	)

	$filteredModels = $Models
	if ($ExcludedModelNames -and $ExcludedModelNames.Count -gt 0) {
		# Exclude any usage rows whose parsed base model name is already selected,
		# regardless of SKU or format.
		$filteredModels = @($Models | Where-Object {
			$u = $_
			$name = if ($u.PSObject.Properties['name']) {
				if ($u.name.PSObject.Properties['value']) { $u.name.value } else { $u.name }
			} else { '' }
			if ([string]::IsNullOrWhiteSpace($name)) { return $true }
			$parsedName = (Parse-ModelName -ModelName $name).Name
			-not ($ExcludedModelNames -contains $parsedName)
		})
	}

	if (-not $filteredModels -or $filteredModels.Count -eq 0) {
		if ($AllowSkip) { return $null }
		throw "No models available to select (all models were filtered out)."
	}
	
	$selectedModel = Show-InteractiveMenu -Items $filteredModels -Title $Title `
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
			# Prefer precomputed availability from $finalUsage.
			# Convention: Available == -1 means "n/a" (no limit returned).
			$available = -1
			if ($u.PSObject.Properties['Available']) {
				$available = [decimal]$u.Available
			} else {
				$hasCurrent = $u.PSObject.Properties['currentValue']
				$hasLimit = $u.PSObject.Properties['limit']
				$current = if ($hasCurrent) { [decimal]$u.currentValue } else { 0 }
				$limit = if ($hasLimit) { [decimal]$u.limit } else { $null }
				$available = if ($limit -ne $null) { $limit - $current } else { -1 }
			}
			
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

# Cache for the (potentially large) Azure model catalog so we only call `az` once
$script:CognitiveModelCatalog = $null

function Get-CognitiveModelCatalog {
	param(
		[Parameter(Mandatory)] [string] $SubscriptionId,
		[Parameter(Mandatory)] [string] $Location
	)

	if ($null -ne $script:CognitiveModelCatalog) {
		return $script:CognitiveModelCatalog
	}

	Write-Host "Fetching Azure Cognitive Services model catalog..."
	try {
		$raw = az cognitiveservices model list --subscription $SubscriptionId --location $Location 2>$null
		if ([string]::IsNullOrWhiteSpace($raw)) {
			$script:CognitiveModelCatalog = @()
		} else {
			$script:CognitiveModelCatalog = @($raw | ConvertFrom-Json)
		}
	} catch {
		$script:CognitiveModelCatalog = @()
	}

	return $script:CognitiveModelCatalog
}

function Get-ModelVersionsForParsedModel {
	param(
		[Parameter(Mandatory)] [array] $Catalog,
		[Parameter(Mandatory)] $ParsedModel
	)

	if (-not $Catalog -or $Catalog.Count -eq 0) {
		return @()
	}

	$matches = $Catalog | Where-Object {
		$_.model.name -eq $ParsedModel.Name -and
		$_.model.format -eq $ParsedModel.Format -and
		@($_.model.skus | Where-Object { $_.name -eq $ParsedModel.Sku }).Count -gt 0
	}

	if (-not $matches -or $matches.Count -eq 0) {
		return @()
	}

	# Sort versions descending and de-dupe by the version string (no Group-Object)
	return @($matches | Sort-Object { [string]$_.model.version } -Descending -Unique)
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
	$current = if ($hasCurrent) { [decimal]$u.currentValue } else { 0 }
	$limit = if ($hasLimit) { [decimal]$u.limit } else { $null }
	# Convention: Available == -1 means "n/a" (no limit returned).
	$available = if ($limit -ne $null) { $limit - $current } else { -1 }
	$currentDisplay = if ($hasCurrent) { $current } else { 'n/a' }
	$limitDisplay = if ($hasLimit) { $limit } else { 'n/a' }
	$availableDisplay = if ($available -ge 0) { $available } else { 'n/a' }
	
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
	$displayText += " | used: $currentDisplay | limit: $limitDisplay"
	$displayText += " | available: $availableDisplay"
	
	# Add DisplayText property to the object
	$u | Add-Member -NotePropertyName 'DisplayText' -NotePropertyValue $displayText -Force
	$u | Add-Member -NotePropertyName 'Current' -NotePropertyValue $current -Force
	$u | Add-Member -NotePropertyName 'Limit' -NotePropertyValue ($limit ?? 0) -Force
	$u | Add-Member -NotePropertyName 'Available' -NotePropertyValue $available -Force
	$u | Add-Member -NotePropertyName 'CurrentDisplay' -NotePropertyValue $currentDisplay -Force
	$u | Add-Member -NotePropertyName 'LimitDisplay' -NotePropertyValue $limitDisplay -Force
	$u | Add-Member -NotePropertyName 'AvailableDisplay' -NotePropertyValue $availableDisplay -Force
	$u
} | Sort-Object DisplayText

if ($needsAgentModel) {
	# Agent model selection
	$excludedModelNames = @()

	$selectedModel = Select-Model -Models $finalUsage -Title "Select Agent Model (hint: filter by 'gpt')" -ContextLines $contextLines

$modelName = if ($selectedModel.PSObject.Properties['name']) {
	if ($selectedModel.name.PSObject.Properties['value']) { $selectedModel.name.value } else { $selectedModel.name }
} else { 'unknown' }

$parsed = Parse-ModelName -ModelName $modelName

if (-not ($excludedModelNames -contains $parsed.Name)) {
	$excludedModelNames += $parsed.Name
}

# Add placeholder to context
$contextLines += "Agent Model: ..."

# Fetch available versions for the selected model (uses one-time cached catalog)
$catalog = Get-CognitiveModelCatalog -SubscriptionId $selectedSub.id -Location $selectedLoc
$modelVersions = Get-ModelVersionsForParsedModel -Catalog $catalog -ParsedModel $parsed

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

# Get quota available for agent model (precomputed in $finalUsage)
$agentAvailable = $selectedModel.AvailableDisplay

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

$selectedEmbedModel = Select-Model -Models $finalUsage -Title "Select Embedding Model for AI Search (hint: filter by 'embedding' or press Esc to skip)" -AllowSkip $true -ContextLines $contextLines -ExcludedModelNames $excludedModelNames

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

	if (-not ($excludedModelNames -contains $embedParsed.Name)) {
		$excludedModelNames += $embedParsed.Name
	}

	# Fetch available versions for the selected embedding model
	$catalog = Get-CognitiveModelCatalog -SubscriptionId $selectedSub.id -Location $selectedLoc
	$embedVersions = Get-ModelVersionsForParsedModel -Catalog $catalog -ParsedModel $embedParsed

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
	$embedAvailable = $selectedEmbedModel.AvailableDisplay
	
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
	
	$selectedAdditionalModel = Select-Model -Models $finalUsage -Title "Select Additional Model (or press Esc to finish)" -AllowSkip $true -ContextLines $contextLines -ExcludedModelNames $excludedModelNames
	
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

	if (-not ($excludedModelNames -contains $additionalParsed.Name)) {
		$excludedModelNames += $additionalParsed.Name
	}
	
	# Fetch available versions for the additional model
	$catalog = Get-CognitiveModelCatalog -SubscriptionId $selectedSub.id -Location $selectedLoc
	$additionalVersions = Get-ModelVersionsForParsedModel -Catalog $catalog -ParsedModel $additionalParsed
	
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
	$additionalAvailable = $selectedAdditionalModel.AvailableDisplay
	
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
	Write-Host 'Saving selections to azd environment...'

	# Save subscription, region, and resource group (only if missing)
	if ($needsSubscription) { azd env set AZURE_SUBSCRIPTION_ID $selectedSub.id | Out-Null }
	if ($needsLocation) { azd env set AZURE_LOCATION $selectedLoc | Out-Null }
	if ($needsResourceGroup -and -not [string]::IsNullOrWhiteSpace($rgName)) { azd env set AZURE_RESOURCE_GROUP $rgName | Out-Null }

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
	$escapedJson = $jsonArray -replace '"', '\\"'
	azd env set AZURE_AI_MODELS $escapedJson | Out-Null
	if ($additionalModels.Count -gt 0) {
		Write-Host "Saved $($additionalModels.Count) additional model(s) to AZURE_AI_MODELS"
	} else {
		Write-Host "No additional models selected (saved empty array to AZURE_AI_MODELS)"
	}

	Write-Host 'Done. Selections saved.'
} else {
	# No model prompting required; only set missing subscription/location/RG if needed
	Write-Host ''
	Write-Host 'Model already configured; skipping model selection.' -ForegroundColor Green
	if ($needsSubscription) { azd env set AZURE_SUBSCRIPTION_ID $selectedSub.id | Out-Null }
	if ($needsLocation) { azd env set AZURE_LOCATION $selectedLoc | Out-Null }
	if ($needsResourceGroup -and -not [string]::IsNullOrWhiteSpace($rgName)) { azd env set AZURE_RESOURCE_GROUP $rgName | Out-Null }
	Write-Host 'Done.' -ForegroundColor Green
}

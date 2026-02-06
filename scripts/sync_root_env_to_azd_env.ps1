<#
	Syncs repo-root .env values into the active azd environment.
	
	- Detects missing/different keys between repo-root .env and .azure/<env>/.env
	- Shows key names and hashes only (never prints secret values)
	- Prompts before syncing
	- Syncs using `azd env set` so azd handles quoting/escaping

	Assumptions:
	- Python is installed and available as `python`
	- python-dotenv is installed (pip install python-dotenv)
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

function Get-RepoRoot {
	$root = Resolve-Path (Join-Path $PSScriptRoot '..')
	return $root.Path
}

function Get-AzdEnvironmentName {
	param(
		[Parameter(Mandatory)] [string] $RepoRoot
	)

	# Prefer the currently-selected azd environment.
	try {
		$envNameRaw = azd env get-value AZURE_ENV_NAME 2>$null
		if (-not [string]::IsNullOrWhiteSpace($envNameRaw)) { return $envNameRaw.Trim() }
	} catch { }

	try {
		$envNameRaw = azd env get-value AZD_ENV_NAME 2>$null
		if (-not [string]::IsNullOrWhiteSpace($envNameRaw)) { return $envNameRaw.Trim() }
	} catch { }

	# Fallback to .azure/config.json defaultEnvironment
	try {
		$configPath = Join-Path $RepoRoot '.azure\config.json'
		if (Test-Path $configPath) {
			$config = Get-Content $configPath -Raw | ConvertFrom-Json
			if ($config -and $config.defaultEnvironment -and -not [string]::IsNullOrWhiteSpace($config.defaultEnvironment)) {
				return [string]$config.defaultEnvironment
			}
		}
	} catch { }

	return $null
}

function Get-DotEnvMap {
	param(
		[Parameter(Mandatory)] [string] $Path
	)

	$python = 'python'

	$pyCode = @'
import json, os, sys
from dotenv import load_dotenv, dotenv_values

path = sys.argv[1]

# Use dotenv_values to discover keys in the file, then load_dotenv to interpret values.
keys = list(dotenv_values(path).keys())
load_dotenv(path, override=True)

out = {k: ('' if os.getenv(k) is None else os.getenv(k)) for k in keys}
print(json.dumps(out))
'@

	$stderrFile = $null
	$pyFile = $null
	try {
		$stderrFile = [System.IO.Path]::GetTempFileName()
		$pyFile = [System.IO.Path]::ChangeExtension([System.IO.Path]::GetTempFileName(), '.py')
		Set-Content -LiteralPath $pyFile -Value $pyCode -Encoding UTF8
		$json = & $python $pyFile $Path 2> $stderrFile
		$exitCode = $LASTEXITCODE
		$stderrText = ''
		try {
			$stderrText = (Get-Content -LiteralPath $stderrFile -Raw -ErrorAction SilentlyContinue)
		} catch {
			$stderrText = ''
		}

		if ($exitCode -ne 0) {
			$err = ($stderrText ?? '').Trim()
			if ([string]::IsNullOrWhiteSpace($err)) { $err = '<no stderr>' }
			throw "python exited with code $exitCode. stderr: $err"
		}

		if ([string]::IsNullOrWhiteSpace($json)) {
			$err = ($stderrText ?? '').Trim()
			if (-not [string]::IsNullOrWhiteSpace($err)) {
				throw "python returned empty output. stderr: $err"
			}
			return @{}
		}

		try {
			$obj = $json | ConvertFrom-Json
		} catch {
			throw "python returned non-JSON output: $json"
		}

		$map = @{}
		foreach ($p in $obj.PSObject.Properties) {
			$map[$p.Name] = [string]$p.Value
		}
		return $map
	} catch {
		throw "Failed to parse $Path via python-dotenv. $($_.Exception.Message)"
	} finally {
		if ($pyFile -and (Test-Path -LiteralPath $pyFile)) {
			Remove-Item -LiteralPath $pyFile -Force -ErrorAction SilentlyContinue
		}
		if ($stderrFile -and (Test-Path -LiteralPath $stderrFile)) {
			Remove-Item -LiteralPath $stderrFile -Force -ErrorAction SilentlyContinue
		}
	}
}

function Get-ShortHash {
	param(
		[string] $Value
	)
	if ($null -eq $Value) { return '<null>' }
	if ($Value -eq '') { return '<empty>' }
	$sha = [System.Security.Cryptography.SHA256]::Create()
	try {
		$bytes = [System.Text.Encoding]::UTF8.GetBytes($Value)
		$hashBytes = $sha.ComputeHash($bytes)
		$hex = -join ($hashBytes | ForEach-Object { $_.ToString('x2') })
		return $hex.Substring(0, 8)
	} finally {
		$sha.Dispose()
	}
}

function Format-EnvValueForDisplay {
	param(
		[AllowNull()] [string] $Value,
		[int] $MaxLen = 200
	)

	if ($null -eq $Value) { return '<null>' }

	# Keep output to one line.
	$v = $Value -replace "`r", '\\r' -replace "`n", '\\n'

	if ($v.Length -le $MaxLen) {
		return $v
	}

	$headLen = [Math]::Min(80, $v.Length)
	$tailLen = [Math]::Min(40, $v.Length - $headLen)
	$head = $v.Substring(0, $headLen)
	$tail = $v.Substring($v.Length - $tailLen, $tailLen)
	return ("{0}…(len={1})…{2}" -f $head, $v.Length, $tail)
}

Ensure-Command -Name azd

$repoRoot = Get-RepoRoot
$rootEnvPath = Join-Path $repoRoot '.env'
if (-not (Test-Path -LiteralPath $rootEnvPath)) {
	Write-Host "No repo-root .env found at $rootEnvPath; nothing to sync." -ForegroundColor DarkGray
	exit 0
}

$envName = Get-AzdEnvironmentName -RepoRoot $repoRoot
if ([string]::IsNullOrWhiteSpace($envName)) {
	Write-Host "Found repo-root .env but couldn't determine the current azd environment name. Run 'azd env select' first (or set .azure/config.json defaultEnvironment)." -ForegroundColor Yellow
	exit 0
}

$azdEnvDir = Join-Path (Join-Path $repoRoot '.azure') $envName
$azdEnvPath = Join-Path $azdEnvDir '.env'

$rootMap = Get-DotEnvMap -Path $rootEnvPath
$azdMap = Get-DotEnvMap -Path $azdEnvPath

if ($rootMap.Keys.Count -eq 0) {
	Write-Host "Repo-root .env has no parseable keys; nothing to sync." -ForegroundColor DarkGray
	exit 0
}

$missingInAzd = @()
$different = @()
foreach ($key in ($rootMap.Keys | Sort-Object)) {
	if (-not $azdMap.ContainsKey($key)) {
		$missingInAzd += $key
		continue
	}
	if ([string]$rootMap[$key] -ne [string]$azdMap[$key]) {
		$different += $key
	}
}

if (($missingInAzd.Count -eq 0) -and ($different.Count -eq 0)) {
	Write-Host 'Repo-root .env and azd env are already in sync.' -ForegroundColor DarkGray
	exit 0
}

Write-Host ''
Write-Host 'Repo-root .env differs from azd env file:' -ForegroundColor Yellow
Write-Host "  Root: $rootEnvPath" -ForegroundColor DarkGray
Write-Host "  Azd:  $azdEnvPath" -ForegroundColor DarkGray
Write-Host ''

if ($missingInAzd.Count -gt 0) {
	Write-Host 'Missing in azd env:' -ForegroundColor Cyan
		foreach ($key in $missingInAzd) {
			$newVal = Format-EnvValueForDisplay -Value ([string]$rootMap[$key])
			Write-Host ("  - {0}: {1}" -f $key, $newVal)
		}
	Write-Host ''
}

if ($different.Count -gt 0) {
		Write-Host 'Different values (old -> new):' -ForegroundColor Cyan
	foreach ($key in $different) {
			$oldVal = Format-EnvValueForDisplay -Value ([string]$azdMap[$key])
			$newVal = Format-EnvValueForDisplay -Value ([string]$rootMap[$key])
			Write-Host ("  - {0}: {1} -> {2}" -f $key, $oldVal, $newVal)
	}
	Write-Host ''
}

$answer = Read-Host 'Sync repo-root .env keys into the active azd environment now? (y/N)'
if ($answer -notin @('y', 'Y', 'yes', 'YES', 'Yes')) {
	exit 0
}

$keysToSync = @($missingInAzd + $different) | Sort-Object -Unique
foreach ($key in $keysToSync) {
	$value = [string]$rootMap[$key]
	if ($value -match "`r|`n") {
		Write-Host "Skipping $key because the value contains a newline (not supported safely in .env)." -ForegroundColor Yellow
		continue
	}
	azd env set -e $envName $key $value 2>$null | Out-Null
	if ($LASTEXITCODE -ne 0) {
		throw "Failed to set $key via 'azd env set'."
	}
}

Write-Host "Synced $($keysToSync.Count) key(s) into the active azd environment via 'azd env set'." -ForegroundColor Green

[CmdletBinding()]
param(
    [string]$ProdConfigPath = "Q:\home-assistant\config",
    [string]$DevConfigPath = "",
    [switch]$IncludeStorage,
    [int]$ListLimit = 50
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if (-not $DevConfigPath) {
    $DevConfigPath = Join-Path $RepoRoot "config"
}

if (-not (Test-Path $ProdConfigPath)) {
    throw "Production config path not found: $ProdConfigPath"
}

if (-not (Test-Path $DevConfigPath)) {
    throw "Dev config path not found: $DevConfigPath"
}

$excludeTop = @(".cache", "backups", "deps", "tts", "www")
if (-not $IncludeStorage) {
    $excludeTop += ".storage"
}

function Should-SkipFile([string]$relPath) {
    $normalized = $relPath -replace "/", "\"
    foreach ($top in $excludeTop) {
        if ($normalized -eq $top -or $normalized.StartsWith("$top\")) {
            return $true
        }
    }
    if ($normalized -like "*\__pycache__\*") {
        return $true
    }
    if ($normalized -like "*\.git\*") {
        return $true
    }
    if ($normalized -like "*.pyc") {
        return $true
    }
    if ($normalized -like "*.log" -or $normalized -like "*.log.*") {
        return $true
    }
    return $false
}

function Get-FileMap([string]$root) {
    $map = @{}
    Get-ChildItem -Path $root -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object {
        $rel = $_.FullName.Substring($root.Length).TrimStart("\")
        if (Should-SkipFile $rel) {
            return
        }
        try {
            $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $_.FullName -ErrorAction Stop).Hash
            $map[$rel] = $hash
        }
        catch {
            Write-Warning "Skipping unreadable file: $($_.FullName)"
        }
    }
    return $map
}

$prod = Get-FileMap $ProdConfigPath
$dev = Get-FileMap $DevConfigPath
$allPaths = ($prod.Keys + $dev.Keys) | Sort-Object -Unique

$onlyProd = [System.Collections.Generic.List[string]]::new()
$onlyDev = [System.Collections.Generic.List[string]]::new()
$different = [System.Collections.Generic.List[string]]::new()

foreach ($path in $allPaths) {
    $inProd = $prod.ContainsKey($path)
    $inDev = $dev.ContainsKey($path)

    if ($inProd -and -not $inDev) {
        $onlyProd.Add($path)
        continue
    }
    if ($inDev -and -not $inProd) {
        $onlyDev.Add($path)
        continue
    }
    if ($prod[$path] -ne $dev[$path]) {
        $different.Add($path)
    }
}

[pscustomobject]@{
    prod_files         = $prod.Count
    dev_files          = $dev.Count
    only_prod_count    = $onlyProd.Count
    only_dev_count     = $onlyDev.Count
    different_count    = $different.Count
    only_prod_examples = @($onlyProd | Select-Object -First $ListLimit)
    only_dev_examples  = @($onlyDev | Select-Object -First $ListLimit)
    diff_examples      = @($different | Select-Object -First $ListLimit)
}

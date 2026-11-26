param(
    [string]$AppName = "knowledge-bridge-tools-4653",
    [string]$ResourceGroup = "knowledge-bridge",
    [string]$SubscriptionId = "2f482561-182f-4bd5-840b-1dc7d21f0811",
    [switch]$PackageOnly
)

$ErrorActionPreference = "Stop"
if (Test-Path -LiteralPath (Join-Path $PSScriptRoot "app.py")) {
    $sourcePath = $PSScriptRoot
} elseif (Test-Path -LiteralPath (Join-Path $PSScriptRoot "src/app.py")) {
    $sourcePath = Join-Path $PSScriptRoot "src"
} else {
    throw "Cannot find app.py beside this script or inside its src folder."
}
$zipPath = Join-Path $sourcePath "app.zip"

# Only these files are shipped. Local clients, .env, and .venv stay local.
$files = @(
    Get-Item -LiteralPath (Join-Path $sourcePath "app.py")
    Get-Item -LiteralPath (Join-Path $sourcePath "requirements.txt")
    Get-ChildItem -LiteralPath (Join-Path $sourcePath "knowledgebridge_tools") -Filter "*.py" -File -Recurse |
        Where-Object { $_.FullName -notmatch '[\\/]__pycache__[\\/]' }
)
if ((Get-Item -LiteralPath (Join-Path $sourcePath "app.py")).Length -eq 0) {
    throw "src/app.py is empty. Save the HTTP entry point before publishing."
}

Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
$stream = [System.IO.File]::Open($zipPath, [System.IO.FileMode]::Create)
try {
    $archive = [System.IO.Compression.ZipArchive]::new(
        $stream, [System.IO.Compression.ZipArchiveMode]::Create, $true
    )
    try {
        foreach ($file in $files) {
            $entryName = $file.FullName.Substring($sourcePath.Length + 1).Replace('\', '/')
            [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
                $archive, $file.FullName, $entryName
            ) | Out-Null
        }
    } finally { $archive.Dispose() }
} finally { $stream.Dispose() }
Write-Host "Created $zipPath ($($files.Count) files)"
if ($PackageOnly) { return }

function Invoke-Azure {
    & az @args
    if ($LASTEXITCODE -ne 0) { throw "Azure CLI failed (exit code $LASTEXITCODE)." }
}

Invoke-Azure account set --subscription $SubscriptionId
Invoke-Azure webapp config set --resource-group $ResourceGroup --name $AppName --startup-file "python -m uvicorn app:app --host 0.0.0.0 --port 8000" --output none
Invoke-Azure webapp config appsettings set --resource-group $ResourceGroup --name $AppName --settings SCM_DO_BUILD_DURING_DEPLOYMENT=true --output none
Invoke-Azure webapp deploy --resource-group $ResourceGroup --name $AppName --src-path $zipPath --type zip --track-status false

Write-Host "Code published. Allow 2-3 minutes for App Service to start."
Write-Host "Find your MCP URL under App Service > Overview > Default domain, then append /mcp."
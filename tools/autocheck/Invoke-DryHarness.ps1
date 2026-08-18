#requires -Version 7.0
[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$ProjectPath,

    [Parameter(Mandatory)]
    [string]$ConfiguredRenderPath,

    [Parameter(Mandatory)]
    [string]$OutDir,

    [ValidateRange(3, 20)]
    [int]$Runs = 3,

    [string]$ReaperPath = 'C:\Program Files\Reaper\reaper.exe'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$ProjectPath = (Resolve-Path -LiteralPath $ProjectPath).Path
if ([System.IO.Path]::GetExtension($ProjectPath) -ne '.rpp') {
    throw "ProjectPath must be a REAPER .rpp project: $ProjectPath"
}
if (-not (Test-Path -LiteralPath $ReaperPath -PathType Leaf)) {
    throw "REAPER executable not found: $ReaperPath"
}

$ConfiguredRenderPath = [System.IO.Path]::GetFullPath($ConfiguredRenderPath)
$OutDir = [System.IO.Path]::GetFullPath($OutDir)
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$ProjectText = Get-Content -LiteralPath $ProjectPath -Raw
$FxPattern = '(?m)^\s*<(VST|AU|CLAP|DX|LV2|JS|VIDEO_EFFECT)\b'
if ($ProjectText -match $FxPattern) {
    throw 'Dry Harness rejected the project: at least one FX block was found in the RPP.'
}

$ExistingOutputs = @()
for ($Index = 1; $Index -le $Runs; $Index++) {
    $Target = Join-Path $OutDir ("D0_{0}.wav" -f $Index)
    if (Test-Path -LiteralPath $Target) { $ExistingOutputs += $Target }
}
if ($ExistingOutputs.Count -gt 0) {
    throw "Dry Harness will not overwrite existing outputs: $($ExistingOutputs -join ', ')"
}
if (Test-Path -LiteralPath $ConfiguredRenderPath) {
    throw "Configured render target already exists; move it before the run: $ConfiguredRenderPath"
}

$Rows = @()
for ($Index = 1; $Index -le $Runs; $Index++) {
    Write-Host "D0 render $Index/$Runs"
    $StartedUtc = [DateTime]::UtcNow
    $Process = Start-Process -FilePath $ReaperPath -ArgumentList @(
        '-renderproject',
        ('"{0}"' -f $ProjectPath)
    ) -Wait -PassThru
    if ($Process.ExitCode -ne 0) {
        throw "REAPER render $Index failed with exit code $($Process.ExitCode)."
    }
    if (-not (Test-Path -LiteralPath $ConfiguredRenderPath -PathType Leaf)) {
        throw "REAPER exited successfully but configured WAV was not created: $ConfiguredRenderPath"
    }
    $Target = Join-Path $OutDir ("D0_{0}.wav" -f $Index)
    Move-Item -LiteralPath $ConfiguredRenderPath -Destination $Target
    $Item = Get-Item -LiteralPath $Target
    $Rows += [ordered]@{
        run = $Index
        project = $ProjectPath
        output = $Target
        bytes = $Item.Length
        sha256 = (Get-FileHash -LiteralPath $Target -Algorithm SHA256).Hash.ToLowerInvariant()
        started_utc = $StartedUtc.ToString('o')
        completed_utc = [DateTime]::UtcNow.ToString('o')
        reaper_exit_code = $Process.ExitCode
    }
}

$Manifest = [ordered]@{
    schema_version = 1
    generated_utc = [DateTime]::UtcNow.ToString('o')
    project_sha256 = (Get-FileHash -LiteralPath $ProjectPath -Algorithm SHA256).Hash.ToLowerInvariant()
    fx_blocks_detected = $false
    runs = $Rows
}
$ManifestPath = Join-Path $OutDir 'dry_harness_runs.json'
$Manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $ManifestPath -Encoding utf8NoBOM

Write-Host "Dry Harness renders created: $OutDir"
Write-Host "Run manifest: $ManifestPath"
Write-Host 'Run Invoke-Ozone12Checks.ps1 to evaluate sample determinism.'

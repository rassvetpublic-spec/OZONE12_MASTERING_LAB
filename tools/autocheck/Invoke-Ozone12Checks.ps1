#requires -Version 7.0
[CmdletBinding()]
param(
    [ValidateSet('Repository', 'P0', 'All')]
    [string]$Mode = 'All',

    [string]$P0Config,

    [string]$OutDir,

    [string]$PythonPath,

    [string]$ReaperPath = 'C:\Program Files\Reaper\reaper.exe',

    [string]$OzoneVst3Path = 'C:\Program Files\Common Files\VST3\iZotope\Ozone 12.vst3'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
if (-not $OutDir) {
    $OutDir = Join-Path $RepoRoot 'reports\autocheck'
}
$OutDir = [System.IO.Path]::GetFullPath($OutDir)
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

function Resolve-PythonCommand {
    if ($PythonPath) {
        if (-not (Test-Path -LiteralPath $PythonPath -PathType Leaf)) {
            throw "PythonPath not found: $PythonPath"
        }
        return [pscustomobject]@{ File = $PythonPath; Prefix = @() }
    }
    $Python = Get-Command python -ErrorAction SilentlyContinue
    if ($Python) {
        return [pscustomobject]@{ File = $Python.Source; Prefix = @() }
    }
    $Py = Get-Command py -ErrorAction SilentlyContinue
    if ($Py) {
        return [pscustomobject]@{ File = $Py.Source; Prefix = @('-3.12') }
    }
    throw 'Python 3.12 was not found. Install it or pass -PythonPath.'
}

function Invoke-Python {
    param([Parameter(Mandatory)][string[]]$Arguments)
    $Command = Resolve-PythonCommand
    & $Command.File @($Command.Prefix) @Arguments | Out-Host
    $Code = $LASTEXITCODE
    return [int]$Code
}

function Get-FirstLine {
    param([Parameter(Mandatory)][string]$CommandName, [string[]]$Arguments = @())
    $Command = Get-Command $CommandName -ErrorAction SilentlyContinue
    if (-not $Command) { return $null }
    try {
        return (& $Command.Source @Arguments 2>&1 | Select-Object -First 1).ToString()
    }
    catch {
        return $null
    }
}

function Get-FileVersionSafe {
    param([Parameter(Mandatory)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { return $null }
    $Candidate = Get-Item -LiteralPath $Path
    if ($Candidate.PSIsContainer) {
        $Candidate = Get-ChildItem -LiteralPath $Path -Recurse -File -ErrorAction SilentlyContinue |
            Where-Object { $_.Extension -in '.dll', '.vst3', '.exe' } |
            Sort-Object Length -Descending |
            Select-Object -First 1
    }
    if (-not $Candidate) { return $null }
    return $Candidate.VersionInfo.FileVersion
}

function Get-Sha256Safe {
    param([Parameter(Mandatory)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $null }
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Write-EnvironmentSnapshot {
    param([Parameter(Mandatory)][string]$Path)
    $Python = Resolve-PythonCommand
    $PythonVersion = (& $Python.File @($Python.Prefix) -c 'import platform; print(platform.python_version())').Trim()
    $PythonPackages = (& $Python.File @($Python.Prefix) -c 'import json, importlib.metadata as m; names=("numpy","scipy"); print(json.dumps({n:(m.version(n) if any(d.metadata.get("Name","").lower()==n for d in m.distributions()) else None) for n in names}))') |
        ConvertFrom-Json
    $OsCaption = $null
    $OsVersion = [System.Environment]::OSVersion.VersionString
    try {
        $Os = Get-CimInstance Win32_OperatingSystem -ErrorAction Stop
        $OsCaption = $Os.Caption
        $OsVersion = $Os.Version
    }
    catch {
        $OsCaption = [System.Runtime.InteropServices.RuntimeInformation]::OSDescription
    }
    $Ffmpeg = Get-Command ffmpeg -ErrorAction SilentlyContinue
    $Ffprobe = Get-Command ffprobe -ErrorAction SilentlyContinue
    $Snapshot = [ordered]@{
        schema_version = 1
        captured_utc = [DateTime]::UtcNow.ToString('o')
        os = [ordered]@{
            caption = $OsCaption
            version = $OsVersion
            architecture = [System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString()
        }
        powershell_version = $PSVersionTable.PSVersion.ToString()
        python_version = ($PythonVersion -split '\.')[0..1] -join '.'
        python_full_version = $PythonVersion
        python_packages = [ordered]@{
            numpy = $PythonPackages.numpy
            scipy = $PythonPackages.scipy
        }
        reaper = [ordered]@{
            path = $ReaperPath
            exists = Test-Path -LiteralPath $ReaperPath -PathType Leaf
            file_version = Get-FileVersionSafe -Path $ReaperPath
        }
        ozone_vst3 = [ordered]@{
            path = $OzoneVst3Path
            exists = Test-Path -LiteralPath $OzoneVst3Path
            file_version = Get-FileVersionSafe -Path $OzoneVst3Path
        }
        ffmpeg_version = Get-FirstLine -CommandName 'ffmpeg' -Arguments @('-version')
        ffprobe_version = Get-FirstLine -CommandName 'ffprobe' -Arguments @('-version')
        analyzer_hashes = [ordered]@{
            autocheck = Get-Sha256Safe -Path (Join-Path $PSScriptRoot 'oz12_autocheck.py')
            mastering_meter = Get-Sha256Safe -Path (Join-Path $RepoRoot 'tools\stage_toolkit\oz12_mastering_meter.py')
        }
        required_binaries = [ordered]@{
            python = $true
            reaper = Test-Path -LiteralPath $ReaperPath -PathType Leaf
            ozone_vst3 = Test-Path -LiteralPath $OzoneVst3Path
            ffmpeg = $null -ne $Ffmpeg
            ffprobe = $null -ne $Ffprobe
            numpy = $null -ne $PythonPackages.numpy
            scipy = $null -ne $PythonPackages.scipy
        }
    }
    $Snapshot | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $Path -Encoding utf8NoBOM
}

$Engine = Join-Path $PSScriptRoot 'oz12_autocheck.py'
if (-not (Test-Path -LiteralPath $Engine -PathType Leaf)) {
    throw "Autocheck engine not found: $Engine"
}

$ExitCode = 0
Push-Location $RepoRoot
try {
    switch ($Mode) {
        'Repository' {
            $ExitCode = Invoke-Python -Arguments @($Engine, 'repo', '--outdir', (Join-Path $OutDir 'repository'))
        }
        'P0' {
            if (-not $P0Config) { throw '-P0Config is required for Mode P0.' }
            $P0Config = (Resolve-Path -LiteralPath $P0Config).Path
            $Environment = Join-Path $OutDir 'environment_observed.json'
            Write-EnvironmentSnapshot -Path $Environment
            $ExitCode = Invoke-Python -Arguments @(
                $Engine, 'p0', '--config', $P0Config,
                '--observed-environment', $Environment,
                '--outdir', (Join-Path $OutDir 'p0')
            )
        }
        'All' {
            if (-not $P0Config) { throw '-P0Config is required for Mode All.' }
            $P0Config = (Resolve-Path -LiteralPath $P0Config).Path
            $Environment = Join-Path $OutDir 'environment_observed.json'
            Write-EnvironmentSnapshot -Path $Environment
            $ExitCode = Invoke-Python -Arguments @(
                $Engine, 'all', '--config', $P0Config,
                '--observed-environment', $Environment,
                '--outdir', $OutDir
            )
        }
    }
}
finally {
    Pop-Location
}

Write-Host "Autocheck exit code: $ExitCode"
Write-Host "Reports: $OutDir"
exit $ExitCode

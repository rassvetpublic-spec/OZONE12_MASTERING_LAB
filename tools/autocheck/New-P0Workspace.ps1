#requires -Version 7.0
[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter(Mandatory)]
    [string]$Root,

    [ValidateSet('L2', 'L3')]
    [string]$SelectedBackend = 'L2',

    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$Root = [System.IO.Path]::GetFullPath($Root)
$ConfigPath = Join-Path $Root 'p0_config.json'

if ((Test-Path -LiteralPath $ConfigPath) -and -not $Force) {
    throw "Config already exists: $ConfigPath. Use -Force only when replacement is intended."
}
if (-not $PSCmdlet.ShouldProcess($Root, 'Create external P0 evidence workspace')) {
    return
}

$Directories = @(
    'input',
    'p0_1_dry',
    'l4',
    'backend_repeats',
    'negative\wrong_target_hash\output',
    'negative\api_failure\output',
    'negative\readback_mismatch\output',
    'reports'
)
foreach ($State in 'S0', 'S1', 'S2') {
    foreach ($Backend in 'L0', 'L1', 'L2', 'L3') {
        $Directories += "states\$State\$Backend"
    }
}
foreach ($Directory in $Directories) {
    New-Item -ItemType Directory -Force -Path (Join-Path $Root $Directory) | Out-Null
}

$States = [ordered]@{}
foreach ($State in 'S0', 'S1', 'S2') {
    $Backends = [ordered]@{}
    foreach ($Backend in 'L0', 'L1', 'L2', 'L3') {
        $Base = "states/$State/$Backend"
        $Backends[$Backend] = [ordered]@{
            wav = "$Base/render.wav"
            readback = "$Base/readback.json"
        }
    }
    $States[$State] = $Backends
}

$Config = [ordered]@{
    schema_version = 1
    expected_environment = [ordered]@{
        os = [ordered]@{
            caption_contains = 'Windows 11'
            architecture = 'X64'
        }
        powershell_version = '7.6.3'
        python_version = '3.12'
        reaper = [ordered]@{
            exists = $true
            file_version_prefix = '7.78'
        }
        ozone_vst3 = [ordered]@{
            exists = $true
            file_version_prefix = '12.0.2'
        }
    }
    expected_plugin = [ordered]@{
        plugin_identity = 'Ozone 12 VST3'
        plugin_version = '120002'
        plugin_build = '1331'
    }
    source_wav = 'input/source.wav'
    dry_renders = @('p0_1_dry/D0_1.wav', 'p0_1_dry/D0_2.wav', 'p0_1_dry/D0_3.wav')
    dry_harness_manifest = 'p0_1_dry/dry_harness_runs.json'
    states = $States
    selected_backend = $SelectedBackend
    backend_repeat_renders = @(
        'backend_repeats/repeat_1.wav',
        'backend_repeats/repeat_2.wav',
        'backend_repeats/repeat_3.wav'
    )
    l4_probe = [ordered]@{ readback = 'l4/readback.json' }
    negative_tests = @(
        [ordered]@{
            name = 'wrong_target_hash'
            result = 'negative/wrong_target_hash/result.json'
            output_dir = 'negative/wrong_target_hash/output'
        },
        [ordered]@{
            name = 'api_failure'
            result = 'negative/api_failure/result.json'
            output_dir = 'negative/api_failure/output'
        },
        [ordered]@{
            name = 'readback_mismatch'
            result = 'negative/readback_mismatch/result.json'
            output_dir = 'negative/readback_mismatch/output'
        }
    )
}

New-Item -ItemType Directory -Force -Path $Root | Out-Null
$Config | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $ConfigPath -Encoding utf8NoBOM
Write-Host "P0 workspace created: $Root"
Write-Host "Config: $ConfigPath"

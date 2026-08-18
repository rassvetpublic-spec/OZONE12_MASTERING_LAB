param(
  [Parameter(Mandatory=$true)][string]$InputXml,
  [Parameter(Mandatory=$true)][string]$OutputXml,
  [switch]$BaselineTS,
  [double[]]$Transient,
  [double[]]$Sustain,
  [int]$Target = -1,
  [switch]$AddMissing,
  [string]$Python = 'python'
)
$script = Join-Path $PSScriptRoot 'patch_ozone_stabilizer.py'
$argsList = @($script,$InputXml,$OutputXml)
if ($BaselineTS) { $argsList += '--baseline-ts' }
if ($Transient) { if ($Transient.Count -ne 6) { throw 'Transient must contain 6 values: Amount Speed Smoothing Low Mid High' }; $argsList += '--t'; $argsList += $Transient }
if ($Sustain) { if ($Sustain.Count -ne 6) { throw 'Sustain must contain 6 values: Amount Speed Smoothing Low Mid High' }; $argsList += '--s'; $argsList += $Sustain }
if ($Target -ge 0) { $argsList += @('--target',$Target) }
if ($AddMissing) { $argsList += '--add-missing' }
& $Python @argsList

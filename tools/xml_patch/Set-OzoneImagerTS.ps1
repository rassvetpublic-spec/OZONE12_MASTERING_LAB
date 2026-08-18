cls
param(
  [Parameter(Mandatory=$true)][string]$InputXml,
  [Parameter(Mandatory=$true)][string]$OutputXml,
  [ValidateSet('safe','strong','extreme')][string]$Preset = 'strong',
  [string]$Python = 'python'
)
$script = Join-Path $PSScriptRoot 'patch_ozone_imager_ts.py'
& $Python $script $InputXml $OutputXml --preset $Preset

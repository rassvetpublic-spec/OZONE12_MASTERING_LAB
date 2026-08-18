cls
param(
    [Parameter(Mandatory=$true)][string]$XmlIn,
    [Parameter(Mandatory=$true)][string]$PatchJson,
    [Parameter(Mandatory=$true)][string]$XmlOut
)

$ErrorActionPreference = 'Stop'
$script = Join-Path $PSScriptRoot '..\patch_ozone_xml_params.py'
python $script --in $XmlIn --patch $PatchJson --out $XmlOut
Write-Host "Done: $XmlOut"

cls
param(
    [Parameter(Mandatory=$true)] [string]$InputXml,
    [Parameter(Mandatory=$true)] [string]$OutputXml,
    [ValidateSet('streaming-safe','wow-pop','codec-safe','loud-probe')] [string]$Profile = 'streaming-safe'
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Py = Join-Path $ScriptDir 'patch_ozone_maximizer.py'
python $Py $InputXml $OutputXml --profile $Profile

Write-Host "Done. Open the XML in Ozone and verify: Maximizer visible, last in chain, Gain Match Off, True Peak On." -ForegroundColor Green

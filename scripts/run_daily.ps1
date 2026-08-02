$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

$ProjectSrc = Join-Path $ProjectRoot "src"
if ([string]::IsNullOrWhiteSpace($env:PYTHONPATH)) {
    $env:PYTHONPATH = $ProjectSrc
} else {
    $env:PYTHONPATH = "$ProjectSrc$([System.IO.Path]::PathSeparator)$env:PYTHONPATH"
}

py -3 -m radar.cli --send-feishu

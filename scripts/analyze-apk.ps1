[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$ApkPath
)

$ErrorActionPreference = 'Stop'
$repository = Split-Path -Parent $PSScriptRoot
$resolvedApk = (Resolve-Path -LiteralPath $ApkPath).Path
$required = @('jadx', 'apktool', 'apkanalyzer', 'keytool')
$missing = @($required | Where-Object { -not (Get-Command $_ -ErrorAction SilentlyContinue) })
if ($missing.Count) {
    throw ('Missing required tools: ' + ($missing -join ', '))
}

$outputRoot = Join-Path $repository 'output'
$jadxOutput = Join-Path $outputRoot 'jadx'
$apktoolOutput = Join-Path $outputRoot 'apktool'
$reportRoot = Join-Path $repository 'reports/local'
$report = Join-Path $reportRoot 'apk-analysis.txt'
New-Item -ItemType Directory -Force -Path $outputRoot, $reportRoot | Out-Null

$hash = Get-FileHash -LiteralPath $resolvedApk -Algorithm SHA256
$package = (& apkanalyzer manifest application-id $resolvedApk).Trim()
$versionName = (& apkanalyzer manifest version-name $resolvedApk).Trim()
$versionCode = (& apkanalyzer manifest version-code $resolvedApk).Trim()

& jadx --show-bad-code --deobf --output-dir $jadxOutput $resolvedApk
if ($LASTEXITCODE -ne 0) { throw "JADX failed with exit code $LASTEXITCODE" }
& apktool decode --force --output $apktoolOutput $resolvedApk
if ($LASTEXITCODE -ne 0) { throw "Apktool failed with exit code $LASTEXITCODE" }

$certificate = (& keytool -printcert -jarfile $resolvedApk 2>&1) -join [Environment]::NewLine
$lines = @(
    'CP PLUS gCMOB APK analysis',
    ('Generated: ' + (Get-Date).ToString('o')),
    ('APK filename: ' + [IO.Path]::GetFileName($resolvedApk)),
    ('SHA-256: ' + $hash.Hash),
    ('Package: ' + $package),
    ('Version name: ' + $versionName),
    ('Version code: ' + $versionCode),
    '',
    'Signing certificate:',
    $certificate
)
Set-Content -LiteralPath $report -Value $lines -Encoding utf8
Write-Output "Analysis complete: $report"


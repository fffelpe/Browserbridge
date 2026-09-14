$HostName = "site.felipeleal.browserbridge"
$RegPath = "HKCU:\Software\Mozilla\NativeMessagingHosts\$HostName"

if (Test-Path $RegPath) {
    Remove-Item -Path $RegPath -Force
}

$ManifestPath = Join-Path $PSScriptRoot "$HostName.json"
if (Test-Path $ManifestPath) {
    Remove-Item $ManifestPath -Force
}

Write-Host "BrowserBridge Native Host removido."

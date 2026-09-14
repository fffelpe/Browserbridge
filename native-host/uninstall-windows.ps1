$ErrorActionPreference = "Stop"

$HostName = "site.felipeleal.browserbridge"

$RegPath = "HKCU:\Software\Mozilla\NativeMessagingHosts\$HostName"

$ManifestPath = Join-Path `
    $PSScriptRoot `
    "$HostName.json"

Write-Host ""
Write-Host "Removendo BrowserBridge Native Host..."
Write-Host ""

if (Test-Path $RegPath) {

    Remove-Item `
        -Path $RegPath `
        -Force

    Write-Host "Registro removido:"
    Write-Host $RegPath

} else {

    Write-Host "Registro nao encontrado."

}

Write-Host ""

if (Test-Path $ManifestPath) {

    Remove-Item `
        -Path $ManifestPath `
        -Force

    Write-Host "Manifest local removido:"
    Write-Host $ManifestPath

} else {

    Write-Host "Manifest local nao encontrado."

}

Write-Host ""
Write-Host "BrowserBridge Native Host removido."
Write-Host ""
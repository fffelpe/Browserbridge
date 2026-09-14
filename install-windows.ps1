$ErrorActionPreference = "Stop"

$HostName = "site.felipeleal.browserbridge"
$ExtensionId = "browserbridge@felipeleal.site"
$Root = $PSScriptRoot
$Launcher = Join-Path $Root "browserbridge.bat"
$ManifestPath = Join-Path $Root "$HostName.json"

$Manifest = @{
    name = $HostName
    description = "BrowserBridge Native Messaging Host"
    path = $Launcher
    type = "stdio"
    allowed_extensions = @($ExtensionId)
} | ConvertTo-Json -Depth 4

$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($ManifestPath, $Manifest, $Utf8NoBom)

$RegPath = "HKCU:\Software\Mozilla\NativeMessagingHosts\$HostName"
New-Item -Path $RegPath -Force | Out-Null
Set-Item -Path $RegPath -Value $ManifestPath

Write-Host ""
Write-Host "BrowserBridge instalado para o usuário atual."
Write-Host "Manifest: $ManifestPath"
Write-Host "Registro:  $RegPath"
Write-Host ""
Write-Host "Agora carregue a extensão no Firefox em about:debugging."

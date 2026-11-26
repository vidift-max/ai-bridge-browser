# Generates a local Android release keystore and its Base64 representation.
# Passwords are entered interactively by keytool and are never echoed by this script.
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$keystorePath = Join-Path $repoRoot "ai-phone-release.keystore"
$base64Path = Join-Path $repoRoot "ai-phone-release-keystore.b64"

if (Test-Path -LiteralPath $keystorePath) {
    throw "Keystore already exists. Refusing to overwrite the existing signing identity."
}
if (Test-Path -LiteralPath $base64Path) {
    throw "Base64 keystore file already exists. Refusing to overwrite it."
}

$keytoolCommand = Get-Command "keytool" -ErrorAction Stop
$keytoolPath = $keytoolCommand.Source
if ([string]::IsNullOrWhiteSpace($keytoolPath)) { $keytoolPath = $keytoolCommand.Path }
if ([string]::IsNullOrWhiteSpace($keytoolPath)) { throw "Could not resolve the JDK keytool executable." }

Write-Host "Creating the AI Bridge Browser release key."
Write-Host "Enter a strong keystore password when keytool prompts."
Write-Host "For the key password prompt, press ENTER to reuse the keystore password."
Write-Host "Keep both passwords in your password manager. They are not saved by this script."

$keytoolArgs = @("-genkeypair", "-v", "-keystore", $keystorePath, "-alias", "ai-phone-release", "-keyalg", "RSA", "-keysize", "3072", "-validity", "10000")
& $keytoolPath @keytoolArgs
if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $keystorePath)) {
    if (Test-Path -LiteralPath $keystorePath) { Remove-Item -LiteralPath $keystorePath -Force }
    throw "keytool failed. No release key was accepted."
}

try {
    $bytes = [System.IO.File]::ReadAllBytes($keystorePath)
    if ($bytes.Length -eq 0) { throw "Generated keystore is empty." }
    $encoded = [Convert]::ToBase64String($bytes)
    [System.IO.File]::WriteAllText($base64Path, $encoded, [System.Text.Encoding]::ASCII)
}
catch {
    if (Test-Path -LiteralPath $keystorePath) { Remove-Item -LiteralPath $keystorePath -Force }
    if (Test-Path -LiteralPath $base64Path) { Remove-Item -LiteralPath $base64Path -Force }
    throw
}

Write-Host ""
Write-Host "Release keystore created locally."
Write-Host "Keystore: $keystorePath"
Write-Host "Base64 file: $base64Path"
Write-Host "Both files are ignored by Git. Do not upload or commit them."
Write-Host "Add the Base64 contents and passwords directly to GitHub Actions Secrets."
Write-Host "Never paste the keystore, Base64 value, or passwords into chat."

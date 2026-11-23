param(
  [string]$Alias = "ai-phone-release"
)

$ErrorActionPreference = "Stop"

$keytool = Get-Command keytool -ErrorAction SilentlyContinue
if (-not $keytool) {
  throw "keytool não foi encontrado. Instale/abra um JDK 17+ antes de executar."
}

$keystore = Join-Path $PWD "ai-phone-release.keystore"
$storePassword = Read-Host "Senha do keystore"
$keyPassword = Read-Host "Senha da chave"
if ([string]::IsNullOrWhiteSpace($storePassword) -or [string]::IsNullOrWhiteSpace($keyPassword)) {
  throw "As senhas não podem estar vazias."
}

& $keytool.Source -genkeypair `
  -v `
  -keystore $keystore `
  -storetype PKCS12 `
  -alias $Alias `
  -keyalg RSA `
  -keysize 3072 `
  -validity 10000 `
  -storepass $storePassword `
  -keypass $keyPassword `
  -dname "CN=AI-PHONE, OU=AI Bridge Browser, O=AI-PHONE, L=Brazil, C=BR"

$bytes = [System.IO.File]::ReadAllBytes($keystore)
$b64 = [Convert]::ToBase64String($bytes)
$b64Path = Join-Path $PWD "ai-phone-release-keystore.b64"
[System.IO.File]::WriteAllText($b64Path, $b64)

Write-Host ""
Write-Host "KEYSTORE criado: $keystore"
Write-Host "BASE64 criado:   $b64Path"
Write-Host ""
Write-Host "Use estes valores nos GitHub Actions Secrets:"
Write-Host "AI_PHONE_RELEASE_KEYSTORE_B64 = conteúdo de $b64Path"
Write-Host "AI_PHONE_RELEASE_KEY_ALIAS    = $Alias"
Write-Host "AI_PHONE_RELEASE_STORE_PASSWORD = a senha informada"
Write-Host "AI_PHONE_RELEASE_KEY_PASSWORD   = a senha informada"
Write-Host ""
Write-Host "NÃO faça commit desses arquivos. O .gitignore já os protege."

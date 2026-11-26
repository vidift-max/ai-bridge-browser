# AI-PHONE — Release Signing

## Objetivo e estado

O fluxo mantém APK Debug para desenvolvimento e gera APK Release somente no job manual de publicação. O APK Release só pode ser publicado após assinatura criptográfica válida e confirmação de que o certificado corresponde à instalação que receberá a atualização.

Sem os quatro Secrets, o job final falha. Sem a variável de fingerprint, também falha. Não há publicação automática em push ou pull request.

## Segredos necessários

Configure diretamente em GitHub → Settings → Secrets and variables → Actions:

- `AI_PHONE_RELEASE_KEYSTORE_B64` — conteúdo Base64 do keystore local;
- `AI_PHONE_RELEASE_STORE_PASSWORD` — senha do keystore;
- `AI_PHONE_RELEASE_KEY_ALIAS` — alias `ai-phone-release`;
- `AI_PHONE_RELEASE_KEY_PASSWORD` — senha da chave (pode ser a mesma senha do keystore).

Configure também a variável de repositório (não é um Secret):

- `AI_PHONE_EXPECTED_SIGNING_CERT_SHA256` — fingerprint SHA-256 do certificado do APK atualmente instalado, confirmado no dispositivo.

Não cole keystore, Base64, senhas ou tokens no chat. Não registre esses valores em arquivos versionados.

## Gerar a chave localmente no Windows

1. Instale um JDK compatível e confirme que `keytool` está disponível no PowerShell.
2. Na raiz do repositório, execute:
   `powershell -ExecutionPolicy Bypass -File .\scripts\create_ai_phone_release_keystore.ps1`
3. O `keytool` solicitará as senhas e os dados do certificado. Use uma senha forte e guarde-a em um gerenciador de senhas. Na senha da chave, pressione ENTER para reutilizar a senha do keystore, se desejar.
4. O script cria localmente `ai-phone-release.keystore` e `ai-phone-release-keystore.b64`. Ele não imprime o Base64 e não sobrescreve arquivos existentes.
5. Os dois arquivos estão explicitamente ignorados pelo Git. Mantenha cópias de segurança seguras e restritas; perder a chave pode impedir atualizações futuras.
6. Cadastre o Base64 e as senhas diretamente nos quatro GitHub Actions Secrets. Cadastre o fingerprint confirmado em `AI_PHONE_EXPECTED_SIGNING_CERT_SHA256`.

O script não cria nem envia Secrets e não publica versões.

## Regra crítica: preservar a instalação existente

**Não desinstale o aplicativo instalado para contornar uma divergência de certificado.** A desinstalação pode apagar os dados locais.

Uma atualização Android normal exige o mesmo pacote e uma assinatura compatível. Se o certificado do APK instalado não corresponder à chave Release, mantenha o aplicativo instalado e bloqueie a atualização. Primeiro será necessário planejar e testar uma migração/backup de dados segura, com autorização explícita. Não prometa atualização in-place enquanto a compatibilidade não estiver comprovada.

## Verificações de publicação

O job manual:

- exige os quatro Secrets e a variável de fingerprint;
- decodifica o keystore em diretório temporário do runner;
- constrói o APK Release;
- verifica a assinatura com `apksigner`;
- compara o fingerprint do APK gerado com o fingerprint esperado;
- gera SHA-256 e manifesto a partir do APK real;
- publica somente depois de todos os gates passarem.

O job de Release tem permissão `contents: write`; o CI normal não tem essa permissão. Nenhum teste de CI substitui a confirmação física do certificado instalado ou a validação de atualização no Android.

## Play Protect

Uma assinatura Release não garante que o Google Play Protect nunca apresente avisos ao instalar APK fora da Google Play. Não tente desativar ou contornar as proteções do Android.

# M211 — contrato do manifesto do atualizador

## Objetivo

Preparar a passagem entre um APK Android Release assinado e o atualizador interno do AI Bridge Browser, sem publicar uma GitHub Release, instalar o APK ou alterar Secrets.

## Dez rodadas executadas

1. Reauditar o contrato de leitura do atualizador em `UpdateCenterActivity` e `UpdateManifestPolicy`.
2. Confirmar os campos obrigatórios: `packageName`, `versionCode`, `versionName`, `apkAssetName`, `sha256` e `notes`.
3. Confirmar que o APK precisa ser publicado como `app-release.apk` dentro de uma GitHub Release estável.
4. Auditar a configuração de assinatura condicional do Gradle e os quatro Secrets já documentados.
5. Auditar o job manual `release-final` e confirmar que não publica automaticamente uma Release.
6. Atualizar os gatilhos do workflow Android para incluir as branches M210 e M211.
7. Adicionar geração do manifesto a partir dos metadados reais do APK Release, sem valores de versão codificados manualmente.
8. Validar pacote, versionCode, versionName e SHA-256 antes de produzir o manifesto; falhar fechado em metadados inválidos.
9. Separar o manifesto como artefato do GitHub Actions, mantendo APK, manifesto e registro de assinatura verificáveis.
10. Documentar o procedimento e os limites: artefatos de CI não são GitHub Releases; publicação e instalação continuam bloqueadas até autorização e teste.

## Manifesto esperado

```json
{
  "packageName": "com.vidiftmax.aibridgebrowser",
  "versionCode": 1,
  "versionName": "0.1.0",
  "apkAssetName": "app-release.apk",
  "sha256": "<SHA-256 real do APK>",
  "notes": "AI Bridge Browser — versão oficial assinada."
}
```

Os valores de versão e hash são extraídos do APK produzido no job de Release assinado. O manifesto é compatível com o contrato atual do atualizador.

## Segurança e limites

- O job `release-final` continua manual (`workflow_dispatch`) e exige os quatro Secrets de assinatura já documentados.
- Nenhuma chave, senha ou arquivo de keystore foi criado, lido, enviado ou alterado nesta missão.
- O job apenas gera artefatos de Actions. Não cria tag, GitHub Release, upload público nem publicação automática.
- O certificado Release deve permanecer o mesmo em todas as atualizações futuras.
- O APK Debug da M210 tem certificado diferente e não é candidato ao atualizador.
- O botão Atualizar só encontrará uma versão depois que APK e manifesto forem publicados como assets de uma GitHub Release estável.
- Nenhuma instalação física, preservação de dados ou conversa AI-01 ↔ AI-02 foi comprovada.

## Critério de aprovação

PASS de contrato quando o CI validar o build/testes, o job de Release de preparação e o workflow contiver geração fail-closed do manifesto. PASS de Release assinada exige os quatro Secrets e execução manual do job `release-final`. PASS de atualização exige ainda publicação autorizada e teste físico no Android.

## Estado

Em validação. PR Draft, sem merge. AI-01 e AI-02 continuam como único par ativo; AI-03 não faz parte do escopo.

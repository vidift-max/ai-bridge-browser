# M248 — Auditoria das capturas do App Manager e fechamento da identidade visual

Data: 2026-11-26

## Objetivo

Avaliar as duas capturas enviadas pelo usuário à pasta `evidence/ai-phone-package-identity/`, atualizar a avaliação de identidade do AI-PHONE e determinar se a evidência já permite liberar uma atualização. Auditoria somente documental; nenhuma instalação, publicação, mesclagem ou alteração de credenciais.

## Fontes verificadas

- Repositório: `vidift-max/ai-bridge-browser`
- Branch: `feat/mission-241-updater-backport-v2-saas-alpha`
- PR #234: aberta, Draft, não mesclada; última leitura nesta missão: head `733a21c4179db2a406c8709c107e4243b0c6cefe`, 16 commits, 44 arquivos, mergeable true.
- Captura 1: `evidence/ai-phone-package-identity/Screenshot_20261126-081930_App Manager.jpg`
  - Blob: `dbcfc7d742748a593f2a4b70215e443c4a374abb`
- Captura 2: `evidence/ai-phone-package-identity/Screenshot_20261126-081942_App Manager.jpg`
  - Blob: `7214f7708b5da87a2a7e1d35fde903bbf03b2cf5`
- Manifest candidato: `app/src/main/AndroidManifest.xml`, blob `dc103c2cfa298c508e38f52e4957e9433d443514`.
- Gradle candidato: `app/build.gradle.kts`, blob `27e5311ee96856ba4edb56cb18100d04d696d5e6`.
- Workflow: `.github/workflows/android-build.yml`, blob `19d050458337158ac08e1e26928407846468f14b`.

## Dez rodadas

### 01/10 — Presença das capturas na pasta de evidências
**PASS.** Duas imagens JPG foram encontradas no diretório esperado do branch.

### 02/10 — Nome visível do aplicativo
**PASS VISUAL.** A primeira captura mostra o título `AI-PHONE` no App Manager.

### 03/10 — Classe da atividade principal
**PASS VISUAL.** A captura mostra `com.vidiftmax.aibridgebrowser.HomeActivity` como atividade principal.

### 04/10 — Inferência do identificador do pacote
**PASS COM LIMITE / EVIDÊNCIA INDIRETA.** O prefixo da classe totalmente qualificada é `com.vidiftmax.aibridgebrowser`, coerente com o namespace e applicationId configurados no Gradle candidato. Isso é forte evidência de identidade, mas não substitui um campo Package Name/Application ID explicitamente exibido pelo Package Manager.

### 05/10 — Comparação com a configuração Gradle
**PASS NO CÓDIGO.** O Gradle candidato declara namespace e applicationId `com.vidiftmax.aibridgebrowser`, versionCode 2 e versionName 0.2.0. A captura não exibe versão instalada, portanto não se conclui que a versão instalada seja 0.1.0 apenas com base nestas imagens.

### 06/10 — SDK e ABI
**PASS VISUAL.** A captura mostra target SDK 35, mínimo 29 e ABI primária `arm64-v8a`. Esses dados descrevem a instalação mostrada; não provam por si só compatibilidade do APK candidato com todos os dispositivos.

### 07/10 — Dados locais do aplicativo
**PASS VISUAL.** A tela mostra 56,02 MB de aplicativo, 8,86 MB de dados e 6,40 MB de cache (total mostrado 71,28 MB). Isso reforça a necessidade de não desinstalar nem limpar dados durante a investigação.

### 08/10 — Instalador atual
**PASS VISUAL.** A segunda captura identifica o instalador e instalador atual como `com.google.android.packageinstaller`. Esse dado não identifica o pacote do AI-PHONE nem comprova a assinatura.

### 09/10 — Limite de identidade e assinatura
**BLOCKED PARCIAL.** As capturas não mostram o campo explícito Package Name/Application ID nem os detalhes do certificado na mesma tela. O fingerprint `861f7689b6502c8dd7b3dcb8f0c9484816e662d8c4cad8ae8da98d5aacfa8ea5` continua registrado apenas como evidência visual anterior do analisador, com emissor Android Debug. Não há vínculo criptográfico independente entre esse fingerprint e o pacote instalado com base apenas nestas duas capturas.

### 10/10 — Decisão de liberação
**NO-GO PARA ATUALIZAÇÃO IN-PLACE.** As imagens são suficientes para classificar a identidade do app como fortemente corroborada por evidência visual indireta, mas não para declarar o Package ID diretamente verificado nem para liberar atualização. Permanecem também as diferenças de paridade funcional do Manifest registradas na M246 e a ausência de prova de certificado Release compatível.

## Matriz final

| Item | Resultado |
|---|---|
| Capturas adicionadas ao repositório | PASS |
| Nome AI-PHONE | PASS visual |
| HomeActivity totalmente qualificada | PASS visual |
| Prefixo de pacote esperado | PASS com evidência indireta |
| Package ID explicitamente exibido | PENDENTE |
| SDK alvo/mínimo e ABI | PASS visual |
| Instalador Android | PASS visual |
| Fingerprint vinculado criptograficamente ao pacote | BLOCKED |
| Paridade funcional do Manifest candidato | NO-GO conforme M246 |
| Atualização in-place | NO-GO / não executar |

## Próxima ação

Não insistir em uma tela que não existe no App Manager utilizado. Se for necessário elevar a prova de indireta para direta, a alternativa técnica é obter uma leitura do PackageInfo do pacote instalado ou analisar um APK exportado do mesmo app, extraindo o package name e o certificado do próprio artefato. Isso pode ser feito em uma etapa futura sem desinstalar o app. Não pedir ao usuário para gerar chaves nem alterar configurações.

## Segurança e escopo

Nenhuma instalação, desinstalação, limpeza de dados, Release, workflow_dispatch, merge, alteração de Secrets ou publicação foi executada. AI-01 e AI-02 permanecem no escopo; AI-03 continua desativada.
